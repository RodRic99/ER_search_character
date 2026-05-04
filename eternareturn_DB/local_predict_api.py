import json
import logging
import os
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
import pymysql
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import Response
from pydantic import BaseModel
from xgboost import XGBRegressor


BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "eternareturn_DB" / "models"

load_dotenv(BASE_DIR / ".env")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("er_predict_api")


class PredictionInput(BaseModel):
    characterNum_1: int
    characterNum_2: int
    characterNum_3: int
    weaponCode_1: int
    weaponCode_2: int
    weaponCode_3: int
    position_main_1: str
    position_main_2: str
    position_main_3: str
    position_sub_1: str
    position_sub_2: str
    position_sub_3: str
    main_melee_cnt: int
    main_ranged_cnt: int
    main_support_cnt: int
    sub_bruiser_cnt: int
    sub_assassin_cnt: int
    sub_poke_cnt: int
    sub_sustain_cnt: int
    sub_util_cnt: int
    sub_tank_cnt: int
    sub_nuker_cnt: int


class LocalPredictor:
    def __init__(self):
        self.conn = pymysql.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            charset="utf8mb4",
        )
        self.model = XGBRegressor()
        self.model.load_model(str(MODEL_DIR / "xgb_model_all_tiers.json"))
        self.feature_names = pd.read_csv(MODEL_DIR / "xgb_model_all_tiers_features.csv")["feature_name"].tolist()
        self.label_encoders = json.loads((MODEL_DIR / "xgb_model_all_tiers_label_encoders.json").read_text(encoding="utf-8"))
        self.character_name_map = {}
        self.weapon_name_map = {}
        self.character_mmr_map = {}
        self.character_synergy_map = {}
        self.character_profile_map = {}
        self.character_weapon_role_map = {}
        self.representative_weapon_map = {}
        self._load_master_maps()
        self._load_feature_stats()

    def _load_master_maps(self):
        character_df = pd.read_sql(
            """
            SELECT
                characterNum,
                characterName,
                default_position_main,
                default_position_sub
            FROM character_master
            """,
            self.conn,
        )
        weapon_df = pd.read_sql("SELECT weaponCode, weaponNameKo FROM weapon_master", self.conn)
        weapon_role_df = pd.read_sql(
            """
            SELECT
                characterNum,
                weaponCode,
                override_position_sub
            FROM character_weapon_role
            """,
            self.conn,
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
        stat_df = pd.read_sql(
            """
            SELECT
                avg_ranktier,
                avg_getmmr,
                characterNum_1,
                weaponCode_1,
                characterNum_2,
                weaponCode_2,
                characterNum_3
                ,weaponCode_3
            FROM rankdb_train_base
            """,
            self.conn,
        )

        high_rank_df = stat_df[stat_df["avg_ranktier"] >= 6000].copy()
        character_long = high_rank_df.melt(
            id_vars=["avg_getmmr"],
            value_vars=["characterNum_1", "characterNum_2", "characterNum_3"],
            var_name="character_slot",
            value_name="characterNum",
        ).dropna(subset=["characterNum", "avg_getmmr"])

        self.character_mmr_map = (
            character_long.groupby("characterNum")["avg_getmmr"]
            .mean()
            .to_dict()
        )

        pair_rows = []
        for _, row in stat_df[["characterNum_1", "characterNum_2", "characterNum_3", "avg_getmmr"]].dropna().iterrows():
            characters = sorted([row["characterNum_1"], row["characterNum_2"], row["characterNum_3"]])
            pair_rows.extend([
                {"pair_key": f"{int(characters[0])}_{int(characters[1])}", "avg_getmmr": row["avg_getmmr"]},
                {"pair_key": f"{int(characters[0])}_{int(characters[2])}", "avg_getmmr": row["avg_getmmr"]},
                {"pair_key": f"{int(characters[1])}_{int(characters[2])}", "avg_getmmr": row["avg_getmmr"]},
            ])

        pair_df = pd.DataFrame(pair_rows)
        self.character_synergy_map = (
            pair_df.groupby("pair_key")["avg_getmmr"]
            .mean()
            .to_dict()
            if not pair_df.empty
            else {}
        )

        weapon_long = stat_df.melt(
            value_vars=["characterNum_1", "characterNum_2", "characterNum_3"],
            var_name="character_slot",
            value_name="characterNum",
        )
        weapon_long["weaponCode"] = stat_df.melt(
            value_vars=["weaponCode_1", "weaponCode_2", "weaponCode_3"],
            var_name="weapon_slot",
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
            weapon_counts.drop_duplicates(subset=["characterNum"])
            .set_index("characterNum")["weaponCode"]
            .to_dict()
        )

    def _combo_to_names(self, character_nums, weapon_codes):
        character_names = [self.character_name_map.get(num, str(num)) for num in character_nums]
        weapon_names = [self.weapon_name_map.get(code, str(code)) for code in weapon_codes]
        return {
            "character_combo_names": "_".join(character_names),
            "weapon_combo_names": "_".join(weapon_names),
            "combo_names": f"{'_'.join(character_names)}|{'_'.join(weapon_names)}",
        }

    def _make_feature_frame(self, payload: PredictionInput):
        row = payload.model_dump()
        return self._make_feature_frame_from_row(row)

    def _make_feature_frame_from_row(self, row):
        character_nums = [row["characterNum_1"], row["characterNum_2"], row["characterNum_3"]]

        row["characterNum_1_avg_getmmr"] = self.character_mmr_map.get(row["characterNum_1"])
        row["characterNum_2_avg_getmmr"] = self.character_mmr_map.get(row["characterNum_2"])
        row["characterNum_3_avg_getmmr"] = self.character_mmr_map.get(row["characterNum_3"])

        sorted_characters = sorted(character_nums)
        pair_keys = [
            f"{sorted_characters[0]}_{sorted_characters[1]}",
            f"{sorted_characters[0]}_{sorted_characters[2]}",
            f"{sorted_characters[1]}_{sorted_characters[2]}",
        ]
        row["character_synergy_1"] = self.character_synergy_map.get(pair_keys[0])
        row["character_synergy_2"] = self.character_synergy_map.get(pair_keys[1])
        row["character_synergy_3"] = self.character_synergy_map.get(pair_keys[2])
        synergy_values = pd.to_numeric(
            pd.Series([row["character_synergy_1"], row["character_synergy_2"], row["character_synergy_3"]]),
            errors="coerce",
        )
        row["character_synergy_mean"] = float(synergy_values.mean()) if synergy_values.notna().any() else np.nan

        frame = pd.DataFrame([row])
        frame = frame.reindex(columns=self.feature_names)

        for col, mapping in self.label_encoders.items():
            if col in frame.columns:
                frame[col] = frame[col].astype(str).map(mapping).fillna(-1).astype("int64")

        return frame

    def _build_row_from_characters(self, character_nums):
        sorted_characters = sorted(int(num) for num in character_nums)
        row = {}
        main_positions = []
        sub_positions = []
        weapon_codes = []

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
            weapon_codes.append(weapon_code)

        row["main_melee_cnt"] = sum(position == "근딜" for position in main_positions)
        row["main_ranged_cnt"] = sum(position == "원딜" for position in main_positions)
        row["main_support_cnt"] = sum(position == "서포터" for position in main_positions)
        row["sub_bruiser_cnt"] = sum(position == "브루저" for position in sub_positions)
        row["sub_assassin_cnt"] = sum(position == "암살" for position in sub_positions)
        row["sub_poke_cnt"] = sum(position == "포킹" for position in sub_positions)
        row["sub_sustain_cnt"] = sum(position == "지속딜" for position in sub_positions)
        row["sub_util_cnt"] = sum(position == "유틸" for position in sub_positions)
        row["sub_tank_cnt"] = sum(position == "탱커" for position in sub_positions)
        row["sub_nuker_cnt"] = sum(position == "누커" for position in sub_positions)

        return row

    def predict_all_character_combinations(self, output_path=None):
        character_nums = sorted(self.character_profile_map.keys())
        rows = []

        for combo in combinations(character_nums, 3):
            row = self._build_row_from_characters(combo)
            rows.append(row)

        feature_frame = pd.concat(
            [self._make_feature_frame_from_row(row) for row in rows],
            ignore_index=True,
        )
        predictions = self.model.predict(feature_frame)

        result_df = pd.DataFrame(rows)
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
        result_df["predicted_avg_getmmr"] = predictions
        result_df = result_df.sort_values("predicted_avg_getmmr", ascending=False).reset_index(drop=True)

        if output_path is not None:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            result_df.to_csv(output_path, index=False, encoding="utf-8-sig")

        return result_df

    def predict(self, payload: PredictionInput):
        frame = self._make_feature_frame(payload)
        prediction = float(self.model.predict(frame)[0])
        character_nums = [payload.characterNum_1, payload.characterNum_2, payload.characterNum_3]
        weapon_codes = [payload.weaponCode_1, payload.weaponCode_2, payload.weaponCode_3]

        return {
            "predicted_avg_getmmr": prediction,
            "input_combo": f"{'_'.join(map(str, sorted(character_nums)))}|{'_'.join(map(str, sorted(weapon_codes)))}",
            **self._combo_to_names(sorted(character_nums), sorted(weapon_codes)),
        }


app = FastAPI(title="ER Local Predict API")
predictor = LocalPredictor()


@app.middleware("http")
async def log_predict_request_body(request: Request, call_next):
    if request.url.path == "/predict":
        body = await request.body()
        print(f"[ER Predict API] Raw /predict body: {body.decode('utf-8', errors='replace')}", flush=True)
        print(f"[ER Predict API] Headers: {dict(request.headers)}", flush=True)

        async def receive():
            return {"type": "http.request", "body": body, "more_body": False}

        request = Request(request.scope, receive)

    return await call_next(request)


@app.put("/predict")
def predict(input_data: PredictionInput):
    payload = input_data.model_dump()
    print(f"[ER Predict API] Received predict payload: {payload}", flush=True)
    logger.warning("Received predict payload: %s", payload)
    result = predictor.predict(input_data)
    print(f"[ER Predict API] Predict result: {result}", flush=True)
    logger.warning("Predict result: %s", result)
    return Response(
        content=json.dumps(result, ensure_ascii=False).encode("utf-8"),
        media_type="application/json; charset=utf-8",
    )
