import json
import os
import re
from datetime import date, datetime, timedelta
from itertools import combinations
from pathlib import Path

import pandas as pd
import pymysql
from dotenv import load_dotenv
from xgboost import XGBRegressor


BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "models"
TABLE_NAME_PATTERN = re.compile(r"^(\d{4}_\d{2}_\d{2})_all_predict$")
INSERT_CHUNK_SIZE = 5000

load_dotenv(BASE_DIR / ".env")


class BatchComboPredictor:
    def __init__(self, model_path=None, feature_path=None, encoder_path=None, max_character_num=83):
        self.conn = pymysql.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            charset="utf8mb4",
            autocommit=False,
        )
        self.database_name = os.getenv("DB_NAME")
        model_path = Path(model_path) if model_path else MODEL_DIR / "xgb_model_all_tiers_rp6100_exp_01.json"
        feature_path = Path(feature_path) if feature_path else MODEL_DIR / "xgb_model_all_tiers_rp6100_exp_01_features.csv"
        encoder_path = Path(encoder_path) if encoder_path else MODEL_DIR / "xgb_model_all_tiers_rp6100_exp_01_label_encoders.json"
        self.model = XGBRegressor()
        self.model.load_model(str(model_path))
        self.feature_names = pd.read_csv(feature_path)["feature_name"].tolist()
        self.label_encoders = json.loads(encoder_path.read_text(encoding="utf-8"))
        self.character_name_map = {}
        self.weapon_name_map = {}
        self.character_profile_map = {}
        self.character_weapon_role_map = {}
        self.character_mmr_map = {}
        self.character_synergy_map = {}
        self.representative_weapon_map = {}
        self._load_master_maps()
        self._load_feature_stats()
        self.character_numbers_for_batch = sorted(
            character_num for character_num in self.character_profile_map.keys() if character_num <= max_character_num
        )

    def close(self):
        self.conn.close()

    def _read_sql(self, query):
        return pd.read_sql(query, self.conn)

    def _load_master_maps(self):
        character_df = self._read_sql(
            """
            SELECT
                characterNum,
                characterName,
                default_position_main,
                default_position_sub
            FROM character_master
            """
        )
        weapon_df = self._read_sql("SELECT weaponCode, weaponNameKo FROM weapon_master")
        weapon_role_df = self._read_sql(
            """
            SELECT
                characterNum,
                weaponCode,
                override_position_sub
            FROM character_weapon_role
            """
        )

        self.character_name_map = dict(zip(character_df["characterNum"], character_df["characterName"]))
        self.weapon_name_map = dict(zip(weapon_df["weaponCode"], weapon_df["weaponNameKo"]))
        self.character_profile_map = {
            int(row["characterNum"]): {
                "characterName": row["characterName"],
                "position_main": row["default_position_main"],
                "position_sub": row["default_position_sub"],
            }
            for _, row in character_df.iterrows()
        }
        self.character_weapon_role_map = {
            (int(row["characterNum"]), int(row["weaponCode"])): row["override_position_sub"]
            for _, row in weapon_role_df.dropna(subset=["characterNum", "weaponCode"]).iterrows()
        }

    def _load_feature_stats(self):
        stat_df = self._read_sql(
            """
            SELECT
                avg_ranktier,
                avg_getmmr,
                characterNum_1,
                weaponCode_1,
                characterNum_2,
                weaponCode_2,
                characterNum_3,
                weaponCode_3
            FROM rankdb_train_base
            """
        )

        high_rank_df = stat_df[stat_df["avg_ranktier"] >= 6000].copy()
        character_long = high_rank_df.melt(
            id_vars=["avg_getmmr"],
            value_vars=["characterNum_1", "characterNum_2", "characterNum_3"],
            value_name="characterNum",
        ).dropna(subset=["characterNum", "avg_getmmr"])
        self.character_mmr_map = character_long.groupby("characterNum")["avg_getmmr"].mean().to_dict()

        pair_rows = []
        for _, row in stat_df[["characterNum_1", "characterNum_2", "characterNum_3", "avg_getmmr"]].dropna().iterrows():
            characters = sorted([int(row["characterNum_1"]), int(row["characterNum_2"]), int(row["characterNum_3"])])
            pair_rows.extend(
                [
                    {"pair_key": f"{characters[0]}_{characters[1]}", "avg_getmmr": row["avg_getmmr"]},
                    {"pair_key": f"{characters[0]}_{characters[2]}", "avg_getmmr": row["avg_getmmr"]},
                    {"pair_key": f"{characters[1]}_{characters[2]}", "avg_getmmr": row["avg_getmmr"]},
                ]
            )

        pair_df = pd.DataFrame(pair_rows)
        self.character_synergy_map = pair_df.groupby("pair_key")["avg_getmmr"].mean().to_dict() if not pair_df.empty else {}

        weapon_long = stat_df.melt(
            value_vars=["characterNum_1", "characterNum_2", "characterNum_3"],
            value_name="characterNum",
        )
        weapon_long["weaponCode"] = stat_df.melt(
            value_vars=["weaponCode_1", "weaponCode_2", "weaponCode_3"],
            value_name="weaponCode",
        )["weaponCode"]
        weapon_long = weapon_long.dropna(subset=["characterNum", "weaponCode"])
        weapon_long["characterNum"] = weapon_long["characterNum"].astype(int)
        weapon_long["weaponCode"] = weapon_long["weaponCode"].astype(int)

        weapon_counts = (
            weapon_long.groupby(["characterNum", "weaponCode"])
            .size()
            .reset_index(name="count")
            .sort_values(["characterNum", "count", "weaponCode"], ascending=[True, False, True])
        )
        self.representative_weapon_map = (
            weapon_counts.drop_duplicates(subset=["characterNum"]).set_index("characterNum")["weaponCode"].to_dict()
        )

    def _build_row_from_characters(self, character_nums):
        sorted_characters = sorted(int(num) for num in character_nums)
        row = {}
        main_positions = []
        sub_positions = []

        for idx, character_num in enumerate(sorted_characters, start=1):
            profile = self.character_profile_map.get(character_num, {})
            weapon_code = int(self.representative_weapon_map.get(character_num, 0))
            position_main = profile.get("position_main")
            position_sub = self.character_weapon_role_map.get(
                (character_num, weapon_code),
                profile.get("position_sub"),
            )

            row[f"characterNum_{idx}"] = character_num
            row[f"weaponCode_{idx}"] = weapon_code
            row[f"position_main_{idx}"] = position_main
            row[f"position_sub_{idx}"] = position_sub
            main_positions.append(position_main)
            sub_positions.append(position_sub)

        row["main_melee_cnt"] = sum(position == "근딜" for position in main_positions)
        row["main_ranged_cnt"] = sum(position == "원딜" for position in main_positions)
        row["main_support_cnt"] = sum(position == "서포터" for position in main_positions)
        row["sub_bruiser_cnt"] = sum(position == "브루저" for position in sub_positions)
        row["sub_assassin_cnt"] = sum(position == "암살" for position in sub_positions)
        row["sub_poke_cnt"] = sum(position == "포킹" for position in sub_positions)
        row["sub_sustain_cnt"] = sum(position == "지속딜" for position in sub_positions)
        row["sub_util_cnt"] = sum(position == "유틸" for position in sub_positions)
        row["sub_tank_cnt"] = sum(position == "탱커" for position in sub_positions)
        row["sub_nuker_cnt"] = sum(position == "폭딜" for position in sub_positions)

        return row

    def _add_stat_features(self, frame):
        frame = frame.copy()
        for idx in [1, 2, 3]:
            frame[f"characterNum_{idx}_avg_getmmr"] = frame[f"characterNum_{idx}"].map(self.character_mmr_map)

        pair_keys = frame.apply(
            lambda row: pd.Series(
                [
                    f"{row['characterNum_1']}_{row['characterNum_2']}",
                    f"{row['characterNum_1']}_{row['characterNum_3']}",
                    f"{row['characterNum_2']}_{row['characterNum_3']}",
                ]
            ),
            axis=1,
        )
        pair_keys.columns = ["pair_key_1", "pair_key_2", "pair_key_3"]
        frame = pd.concat([frame, pair_keys], axis=1)

        frame["character_synergy_1"] = frame["pair_key_1"].map(self.character_synergy_map)
        frame["character_synergy_2"] = frame["pair_key_2"].map(self.character_synergy_map)
        frame["character_synergy_3"] = frame["pair_key_3"].map(self.character_synergy_map)
        frame["character_synergy_mean"] = frame[
            ["character_synergy_1", "character_synergy_2", "character_synergy_3"]
        ].mean(axis=1)

        return frame.drop(columns=["pair_key_1", "pair_key_2", "pair_key_3"])

    def _encode_features(self, frame):
        feature_frame = frame.reindex(columns=self.feature_names)
        for col, mapping in self.label_encoders.items():
            if col in feature_frame.columns:
                feature_frame[col] = feature_frame[col].astype(str).map(mapping).fillna(-1).astype("int64")
        return feature_frame

    def _build_today_table_name(self):
        return f"{date.today().strftime('%Y_%m_%d')}_all_predict"

    def _infer_sql_type(self, series):
        non_null = series.dropna()
        if pd.api.types.is_integer_dtype(series):
            return "INT"
        if pd.api.types.is_float_dtype(series):
            return "DOUBLE"
        if non_null.empty:
            return "VARCHAR(255)"

        max_length = int(non_null.astype(str).map(len).max())
        return f"VARCHAR({max(32, min(max_length, 255))})"

    def _create_prediction_table(self, table_name, result_df):
        column_defs = []
        for column in result_df.columns:
            sql_type = self._infer_sql_type(result_df[column])
            nullable = "NULL" if result_df[column].isnull().any() else "NOT NULL"
            column_defs.append(f"`{column}` {sql_type} {nullable}")

        create_sql = f"""
        CREATE TABLE `{table_name}` (
            `id` BIGINT NOT NULL AUTO_INCREMENT,
            {", ".join(column_defs)},
            PRIMARY KEY (`id`),
            KEY `idx_input_combo` (`input_combo`),
            KEY `idx_predicted_avg_getmmr` (`predicted_avg_getmmr`),
            KEY `idx_character_nums` (`characterNum_1`, `characterNum_2`, `characterNum_3`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """

        with self.conn.cursor() as cursor:
            cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`")
            cursor.execute(create_sql)

    def _normalize_value(self, value):
        if pd.isna(value):
            return None
        if hasattr(value, "item"):
            return value.item()
        return value

    def _insert_prediction_rows(self, table_name, result_df):
        columns = list(result_df.columns)
        column_sql = ", ".join(f"`{column}`" for column in columns)
        placeholder_sql = ", ".join(["%s"] * len(columns))
        insert_sql = f"INSERT INTO `{table_name}` ({column_sql}) VALUES ({placeholder_sql})"

        with self.conn.cursor() as cursor:
            for start_index in range(0, len(result_df), INSERT_CHUNK_SIZE):
                chunk = result_df.iloc[start_index:start_index + INSERT_CHUNK_SIZE]
                values = [
                    tuple(self._normalize_value(value) for value in row)
                    for row in chunk.itertuples(index=False, name=None)
                ]
                cursor.executemany(insert_sql, values)

    def _cleanup_old_prediction_tables(self):
        cutoff_date = date.today() - timedelta(days=1)
        dropped_tables = []

        with self.conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = %s
                """,
                (self.database_name,),
            )
            table_names = [row[0] for row in cursor.fetchall()]

            for table_name in table_names:
                match = TABLE_NAME_PATTERN.match(table_name)
                if not match:
                    continue

                table_date = datetime.strptime(match.group(1), "%Y_%m_%d").date()
                if table_date < cutoff_date:
                    cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`")
                    dropped_tables.append(table_name)

        return dropped_tables

    def predict_all_character_combinations(self):
        rows = [self._build_row_from_characters(combo) for combo in combinations(self.character_numbers_for_batch, 3)]
        result_df = pd.DataFrame(rows)
        result_df = self._add_stat_features(result_df)
        feature_frame = self._encode_features(result_df)
        result_df["predicted_avg_getmmr"] = self.model.predict(feature_frame)
        result_df["input_combo"] = result_df[
            ["characterNum_1", "characterNum_2", "characterNum_3"]
        ].astype(str).agg("_".join, axis=1)
        result_df["character_combo_names"] = result_df[
            ["characterNum_1", "characterNum_2", "characterNum_3"]
        ].apply(
            lambda row: "_".join(self.character_name_map.get(int(num), str(num)) for num in row),
            axis=1,
        )
        result_df["weapon_combo_names"] = result_df[
            ["weaponCode_1", "weaponCode_2", "weaponCode_3"]
        ].apply(
            lambda row: "_".join(self.weapon_name_map.get(int(code), str(code)) for code in row),
            axis=1,
        )
        result_df = result_df.sort_values("predicted_avg_getmmr", ascending=False).reset_index(drop=True)

        table_name = self._build_today_table_name()
        self._create_prediction_table(table_name, result_df)
        self._insert_prediction_rows(table_name, result_df)
        dropped_tables = self._cleanup_old_prediction_tables()
        self.conn.commit()

        return result_df, table_name, dropped_tables


def main():
    predictor = BatchComboPredictor()

    try:
        result_df, table_name, dropped_tables = predictor.predict_all_character_combinations()
    except Exception:
        predictor.conn.rollback()
        raise
    finally:
        predictor.close()

    print(f"Saved table: {table_name}")
    print(f"Rows: {len(result_df)}")
    if dropped_tables:
        print("Dropped old tables:")
        for dropped_table in dropped_tables:
            print(f" - {dropped_table}")
    else:
        print("Dropped old tables: none")

    print("\nTop 10 predictions")
    print(
        result_df[
            [
                "input_combo",
                "character_combo_names",
                "weapon_combo_names",
                "predicted_avg_getmmr",
            ]
        ]
        .head(10)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()
