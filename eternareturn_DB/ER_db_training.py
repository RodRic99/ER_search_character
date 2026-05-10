import pymysql
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os
import warnings
import sklearn
import json
from pathlib import Path

from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import mean_absolute_error, r2_score, root_mean_squared_error
from xgboost import XGBRegressor
from dotenv import load_dotenv

warnings.filterwarnings('ignore')

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

class ERDBClassification:
    def __init__(self):
        self.conn = pymysql.connect(
            host=os.getenv('DB_HOST'),
            port=int(os.getenv('DB_PORT', '3306')),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME'),
            charset='utf8mb4',
        )
        self.df = None
        self.tier_group_dfs = {}
        self.tier_models = {}
        self.tier_results = {}
        self.tier_feature_columns = {}
        self.tier_label_encoders = {}
        self.tier_prediction_samples = {}
        self.character_name_map = {}
        self.weapon_name_map = {}
        self.position_main_map = {}
        self.position_sub_map = {}

    def conect_db(self, rebuild_train_base=False, train_base_table='rankdb_train_base', source_table='rankdb_v2'):
        try:
            if rebuild_train_base:
                self.build_train_base_from_rankdb_v2(
                    source_table=source_table,
                    target_table=train_base_table,
                )
            self.df = pd.read_sql(f"SELECT * FROM `{train_base_table}`", self.conn)
        except pymysql.MySQLError as e:
            print(f"Database connection failed: {e}")

    def load_position_role_maps(self):
        if self.position_main_map and self.position_sub_map:
            return self.position_main_map, self.position_sub_map

        try:
            character_df = pd.read_sql(
                "SELECT characterNum, default_position_main, default_position_sub FROM character_master",
                self.conn,
            )
            cwr_df = pd.read_sql(
                "SELECT characterNum, weaponCode, override_position_sub FROM character_weapon_role",
                self.conn,
            )

            self.position_main_map = dict(
                zip(character_df['characterNum'], character_df['default_position_main'])
            )
            default_sub_map = dict(
                zip(character_df['characterNum'], character_df['default_position_sub'])
            )
            self.position_sub_map = {
                (int(row['characterNum']), int(row['weaponCode'])): row['override_position_sub']
                if pd.notna(row['override_position_sub'])
                else default_sub_map.get(int(row['characterNum']))
                for _, row in cwr_df.iterrows()
            }
            for character_num, default_sub in default_sub_map.items():
                self.position_sub_map.setdefault((int(character_num), None), default_sub)
        except Exception:
            self.position_main_map = {}
            self.position_sub_map = {}

        return self.position_main_map, self.position_sub_map

    def get_latest_patch_start(self, reference_time, patch_weekday=3, patch_hour=16):
        reference_time = pd.Timestamp(reference_time)
        patch_day = reference_time.normalize() + pd.Timedelta(hours=patch_hour)
        days_back = (reference_time.weekday() - patch_weekday) % 7
        patch_day = patch_day - pd.Timedelta(days=days_back)
        if reference_time < patch_day:
            patch_day -= pd.Timedelta(days=7)
        return patch_day

    def build_character_patch_mmrgain_map(
        self,
        raw_df,
        mmr_gain_col='mmrGainInGame',
        patch_weekday=3,
        patch_hour=16,
        patch_days=7,
    ):
        if raw_df.empty or 'characterNum' not in raw_df.columns or mmr_gain_col not in raw_df.columns:
            return {}, None, None

        event_time = pd.to_datetime(raw_df['startDtm'], errors='coerce')
        latest_time = event_time.max()
        if pd.isna(latest_time):
            return {}, None, None

        patch_start = self.get_latest_patch_start(latest_time, patch_weekday=patch_weekday, patch_hour=patch_hour)
        patch_end = patch_start + pd.Timedelta(days=patch_days)

        patch_df = raw_df[(event_time >= patch_start) & (event_time < patch_end)].copy()
        patch_df['characterNum'] = pd.to_numeric(patch_df['characterNum'], errors='coerce')
        patch_df[mmr_gain_col] = pd.to_numeric(patch_df[mmr_gain_col], errors='coerce')
        patch_df = patch_df.dropna(subset=['characterNum', mmr_gain_col])

        character_map = (
            patch_df.groupby('characterNum')[mmr_gain_col]
            .mean()
            .to_dict()
        )
        return character_map, patch_start, patch_end

    def save_dataframe_to_mysql(self, df, table_name, primary_keys=None, chunk_size=1000):
        if df is None or df.empty:
            raise ValueError(f"No data to save into {table_name}.")

        primary_keys = primary_keys or []
        create_df = df.copy()

        def mysql_type(column_name, series):
            dtype = series.dtype
            if pd.api.types.is_integer_dtype(dtype):
                return "BIGINT"
            if pd.api.types.is_float_dtype(dtype):
                return "DOUBLE"
            if pd.api.types.is_bool_dtype(dtype):
                return "TINYINT(1)"
            if pd.api.types.is_datetime64_any_dtype(dtype):
                return "DATETIME"
            if column_name in primary_keys:
                non_null_series = series.dropna().astype(str)
                max_length = int(non_null_series.map(len).max()) if not non_null_series.empty else 32
                if column_name == 'cutoff_date':
                    return "VARCHAR(10)"
                return f"VARCHAR({min(max(max_length, 32), 512)})"
            return "TEXT"

        column_defs = []
        for col in create_df.columns:
            null_sql = "NOT NULL" if col in primary_keys else "DEFAULT NULL"
            column_defs.append(f"`{col}` {mysql_type(col, create_df[col])} {null_sql}")
        pk_sql = f", PRIMARY KEY ({', '.join(f'`{key}`' for key in primary_keys)})" if primary_keys else ""
        create_sql = f"""
        CREATE TABLE `{table_name}` (
            {", ".join(column_defs)}
            {pk_sql}
        ) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
        """

        with self.conn.cursor() as cur:
            cur.execute(f"DROP TABLE IF EXISTS `{table_name}`")
            cur.execute(create_sql)
        self.conn.commit()

        insert_columns = create_df.columns.tolist()
        placeholders = ", ".join(["%s"] * len(insert_columns))
        insert_sql = f"""
        INSERT INTO `{table_name}` ({", ".join(f"`{col}`" for col in insert_columns)})
        VALUES ({placeholders})
        """

        insert_df = create_df.replace({np.nan: None})
        for col in insert_df.columns:
            if pd.api.types.is_datetime64_any_dtype(insert_df[col]):
                insert_df[col] = insert_df[col].where(insert_df[col].notna(), None)

        rows = [tuple(row) for row in insert_df.itertuples(index=False, name=None)]

        with self.conn.cursor() as cur:
            for start in range(0, len(rows), chunk_size):
                cur.executemany(insert_sql, rows[start:start + chunk_size])
        self.conn.commit()

    def build_train_base_from_rankdb_v2(
        self,
        source_table='rankdb_v2',
        target_table='rankdb_train_base',
        patch_weekday=3,
        patch_hour=16,
        patch_days=7,
    ):
        raw_query = f"""
        SELECT
            gameid,
            gamerank,
            player_slot,
            startDtm,
            matchingmode,
            matchingTeamMode,
            teamNumber,
            characterNum,
            bestWeapon,
            damageToPlayer,
            playerKill,
            healAmount,
            mmrBefore,
            mmrGainInGame,
            rankPoint
        FROM `{source_table}`
        """
        raw_df = pd.read_sql(raw_query, self.conn)
        if raw_df.empty:
            raise ValueError(f"{source_table} is empty.")

        numeric_columns = [
            'gamerank', 'player_slot', 'matchingmode', 'matchingTeamMode', 'teamNumber',
            'characterNum', 'bestWeapon', 'damageToPlayer', 'playerKill', 'healAmount',
            'mmrBefore', 'mmrGainInGame', 'rankPoint',
        ]
        for col in numeric_columns:
            if col in raw_df.columns:
                raw_df[col] = pd.to_numeric(raw_df[col], errors='coerce')
        raw_df['startDtm'] = pd.to_datetime(raw_df['startDtm'], errors='coerce')

        raw_df = raw_df.dropna(subset=['gameid', 'teamNumber', 'characterNum', 'bestWeapon', 'startDtm']).copy()
        raw_df = raw_df[raw_df['matchingTeamMode'].fillna(0).astype(int) == 3].copy()
        raw_df = raw_df.sort_values(['gameid', 'teamNumber', 'player_slot', 'characterNum']).reset_index(drop=True)

        team_sizes = raw_df.groupby(['gameid', 'teamNumber']).size()
        valid_teams = team_sizes[team_sizes == 3].index
        raw_df = raw_df.set_index(['gameid', 'teamNumber']).loc[valid_teams].reset_index()

        position_main_map, position_sub_map = self.load_position_role_maps()
        character_patch_mmrgain_map, patch_start, patch_end = self.build_character_patch_mmrgain_map(
            raw_df,
            mmr_gain_col='mmrGainInGame',
            patch_weekday=patch_weekday,
            patch_hour=patch_hour,
            patch_days=patch_days,
        )
        print(
            f"Building {target_table} from {source_table}: "
            f"teams={raw_df.groupby(['gameid', 'teamNumber']).ngroups}, "
            f"patch_window={patch_start} ~ {patch_end}"
        )

        team_rows = []
        grouped = raw_df.groupby(['gameid', 'teamNumber'], sort=False)
        for (gameid, team_number), group in grouped:
            group = group.sort_values(['player_slot', 'characterNum']).reset_index(drop=True)
            first_row = group.iloc[0]
            damage_values = pd.to_numeric(group['damageToPlayer'], errors='coerce').fillna(0.0)
            kill_values = pd.to_numeric(group['playerKill'], errors='coerce').fillna(0.0)
            heal_values = pd.to_numeric(group['healAmount'], errors='coerce').fillna(0.0)

            row = {
                'gameid': int(gameid),
                'teamNumber': int(team_number),
                'gamerank': int(first_row['gamerank']) if pd.notna(first_row['gamerank']) else None,
                'startDtm': first_row['startDtm'],
                'matchingmode': int(first_row['matchingmode']) if pd.notna(first_row['matchingmode']) else None,
                'avg_ranktier': group['mmrBefore'].mean(),
                # Keep the existing column name for compatibility with the training pipeline,
                # but use mmrGainInGame as the underlying team performance signal.
                'avg_getmmr': group['mmrGainInGame'].mean(),
                'avg_rankpoint': group['rankPoint'].mean(),
                'total_damage': float(damage_values.sum()),
                'total_kill': float(kill_values.sum()),
                'avg_damage': float(damage_values.mean()),
                'avg_kill': float(kill_values.mean()),
                'max_damage': float(damage_values.max()),
                'min_damage': float(damage_values.min()),
                'max_kill': float(kill_values.max()),
                'min_kill': float(kill_values.min()),
                'damage_std': float(damage_values.std(ddof=0)),
                'total_healAmount': float(heal_values.sum()),
                'avg_healAmount': float(heal_values.mean()),
            }

            main_positions = []
            sub_positions = []
            patch_mmr_values = []
            for idx, player in enumerate(group.itertuples(index=False), start=1):
                character_num = int(player.characterNum) if pd.notna(player.characterNum) else None
                weapon_code = int(player.bestWeapon) if pd.notna(player.bestWeapon) else None
                position_main = position_main_map.get(character_num)
                position_sub = position_sub_map.get((character_num, weapon_code))
                if position_sub is None:
                    position_sub = position_sub_map.get((character_num, None))

                row[f'characterNum_{idx}'] = character_num
                row[f'weaponCode_{idx}'] = weapon_code
                row[f'position_main_{idx}'] = position_main
                row[f'position_sub_{idx}'] = position_sub
                row[f'damage_{idx}'] = float(player.damageToPlayer) if pd.notna(player.damageToPlayer) else None
                row[f'playerkill_{idx}'] = float(player.playerKill) if pd.notna(player.playerKill) else None
                row[f'healAmount_{idx}'] = float(player.healAmount) if pd.notna(player.healAmount) else None
                row[f'character_avg_mmrgain_{idx}'] = character_patch_mmrgain_map.get(character_num)

                main_positions.append(position_main)
                sub_positions.append(position_sub)
                patch_mmr_values.append(character_patch_mmrgain_map.get(character_num))

            row['team_character_avg_mmrgain'] = float(np.nanmean(patch_mmr_values)) if any(
                pd.notna(val) for val in patch_mmr_values
            ) else None
            highest_mmr_candidates = [
                (
                    idx,
                    group.iloc[idx - 1]['mmrBefore'] if idx - 1 < len(group) else None,
                    row.get(f'characterNum_{idx}'),
                    row.get(f'position_main_{idx}'),
                    row.get(f'position_sub_{idx}'),
                )
                for idx in range(1, 4)
                if idx - 1 < len(group) and pd.notna(group.iloc[idx - 1]['mmrBefore'])
            ]
            if highest_mmr_candidates:
                highest_player_index, _, highest_character_num, highest_position_main, highest_position_sub = max(
                    highest_mmr_candidates,
                    key=lambda item: item[1],
                )
            else:
                highest_player_index, highest_character_num, highest_position_main, highest_position_sub = (None, None, None, None)

            row['highest_mmr_character'] = highest_character_num
            row['highest_mmr_position_main'] = highest_position_main
            row['highest_mmr_position_sub'] = highest_position_sub
            row['highest_mmr_player_1'] = int(highest_player_index == 1)
            row['highest_mmr_player_2'] = int(highest_player_index == 2)
            row['highest_mmr_player_3'] = int(highest_player_index == 3)
            row['main_melee_cnt'] = int(sum(pos == '근딜' for pos in main_positions))
            row['main_ranged_cnt'] = int(sum(pos == '원딜' for pos in main_positions))
            row['main_support_cnt'] = int(sum(pos == '서포터' for pos in main_positions))
            row['sub_bruiser_cnt'] = int(sum(pos == '브루저' for pos in sub_positions))
            row['sub_assassin_cnt'] = int(sum(pos == '암살' for pos in sub_positions))
            row['sub_poke_cnt'] = int(sum(pos == '포킹' for pos in sub_positions))
            row['sub_sustain_cnt'] = int(sum(pos == '지속딜' for pos in sub_positions))
            row['sub_util_cnt'] = int(sum(pos == '유틸' for pos in sub_positions))
            row['sub_tank_cnt'] = int(sum(pos == '탱커' for pos in sub_positions))
            row['sub_nuker_cnt'] = int(sum(pos == '누커' for pos in sub_positions))

            team_rows.append(row)

        train_base_df = pd.DataFrame(team_rows).sort_values(['gameid', 'teamNumber']).reset_index(drop=True)
        self.save_dataframe_to_mysql(
            train_base_df,
            table_name=target_table,
            primary_keys=['gameid', 'teamNumber'],
        )
        return train_base_df

    def build_position_synergy_cache_df(self, train_base_df=None, cutoff_date=None):
        if train_base_df is None:
            if self.df is not None and not self.df.empty:
                train_base_df = self.df.copy()
            else:
                train_base_df = pd.read_sql("SELECT * FROM `rankdb_train_base`", self.conn)

        if train_base_df.empty:
            raise ValueError("No train base data available for position synergy cache.")

        cache_df = train_base_df.copy()
        position_main_cols = ['position_main_1', 'position_main_2', 'position_main_3']
        position_sub_cols = ['position_sub_1', 'position_sub_2', 'position_sub_3']

        for col in position_main_cols + position_sub_cols:
            if col not in cache_df.columns:
                raise ValueError(f"Missing required column for position synergy cache: {col}")

        cache_df['position_main_combo'] = cache_df[position_main_cols].apply(
            lambda row: '_'.join(sorted([str(value) for value in row.tolist() if pd.notna(value)])),
            axis=1,
        )
        cache_df['position_sub_combo'] = cache_df[position_sub_cols].apply(
            lambda row: '_'.join(sorted([str(value) for value in row.tolist() if pd.notna(value)])),
            axis=1,
        )
        cache_df['position_full_combo'] = cache_df.apply(
            lambda row: '|'.join(
                sorted(
                    [
                        f"{row[f'position_main_{idx}']}:{row[f'position_sub_{idx}']}"
                        for idx in range(1, 4)
                        if pd.notna(row.get(f'position_main_{idx}')) and pd.notna(row.get(f'position_sub_{idx}'))
                    ]
                )
            ),
            axis=1,
        )
        cache_df['position_signature'] = (
            cache_df['position_main_combo']
            + '||'
            + cache_df['position_sub_combo']
            + '||'
            + cache_df['position_full_combo']
        )

        grouped = (
            cache_df.groupby(
                ['position_signature', 'position_main_combo', 'position_sub_combo', 'position_full_combo'],
                dropna=False,
            )
            .agg(
                match_count=('gameid', 'size'),
                avg_getmmr=('avg_getmmr', 'mean'),
                avg_rankpoint=('avg_rankpoint', 'mean'),
                avg_ranktier=('avg_ranktier', 'mean'),
                avg_total_damage=('total_damage', 'mean'),
                avg_damage_std=('damage_std', 'mean'),
                avg_total_healAmount=('total_healAmount', 'mean'),
            )
            .reset_index()
            .sort_values(['match_count', 'avg_getmmr'], ascending=[False, False])
            .reset_index(drop=True)
        )

        grouped.insert(0, 'cutoff_date', str(cutoff_date) if cutoff_date is not None else None)
        return grouped

    def save_position_synergy_cache(self, cache_df, table_name='daily_position_synergy_cache'):
        self.save_dataframe_to_mysql(
            cache_df,
            table_name=table_name,
            primary_keys=['cutoff_date', 'position_signature'],
        )
        return table_name

    def load_position_synergy_cache(self, table_name='daily_position_synergy_cache'):
        return pd.read_sql(f"SELECT * FROM `{table_name}`", self.conn)

    def build_absolute_score_cache_df(
        self,
        prediction_df,
        position_synergy_cache_df,
        cutoff_date=None,
    ):
        if prediction_df is None or prediction_df.empty:
            raise ValueError("Prediction dataframe is required to build absolute score cache.")
        if position_synergy_cache_df is None or position_synergy_cache_df.empty:
            raise ValueError("Position synergy cache dataframe is required to build absolute score cache.")

        def summarize_metric(metric_name, series):
            clean_series = pd.to_numeric(series, errors='coerce')
            clean_series = clean_series[np.isfinite(clean_series)]
            if clean_series.empty:
                return None

            return {
                'cutoff_date': str(cutoff_date) if cutoff_date is not None else None,
                'metric_name': metric_name,
                'sample_count': int(clean_series.shape[0]),
                'min_value': float(clean_series.min()),
                'max_value': float(clean_series.max()),
                'p05_value': float(clean_series.quantile(0.05)),
                'p95_value': float(clean_series.quantile(0.95)),
            }

        rows = []
        predicted_row = summarize_metric('predicted_avg_getmmr', prediction_df.get('predicted_avg_getmmr'))
        if predicted_row is not None:
            rows.append(predicted_row)

        synergy_columns = ['character_synergy_1', 'character_synergy_2', 'character_synergy_3']
        synergy_series = pd.concat(
            [prediction_df[col] for col in synergy_columns if col in prediction_df.columns],
            ignore_index=True,
        )
        synergy_row = summarize_metric('character_synergy', synergy_series)
        if synergy_row is not None:
            rows.append(synergy_row)

        position_row = summarize_metric('position_avg_getmmr', position_synergy_cache_df.get('avg_getmmr'))
        if position_row is not None:
            rows.append(position_row)

        if not rows:
            raise ValueError("No score metrics could be summarized.")

        return pd.DataFrame(rows)

    def save_absolute_score_cache(self, cache_df, table_name='daily_score_metric_cache'):
        self.save_dataframe_to_mysql(
            cache_df,
            table_name=table_name,
            primary_keys=['cutoff_date', 'metric_name'],
        )
        return table_name

    def load_absolute_score_cache(self, table_name='daily_score_metric_cache'):
        return pd.read_sql(f"SELECT * FROM `{table_name}`", self.conn)

    def load_master_name_maps(self):
        if self.character_name_map and self.weapon_name_map:
            return self.character_name_map, self.weapon_name_map

        try:
            character_df = pd.read_sql("SELECT characterNum, characterName FROM character_master", self.conn)
            weapon_df = pd.read_sql("SELECT weaponCode, weaponNameKo FROM weapon_master", self.conn)

            self.character_name_map = dict(zip(character_df['characterNum'], character_df['characterName']))
            self.weapon_name_map = dict(zip(weapon_df['weaponCode'], weapon_df['weaponNameKo']))
        except Exception:
            self.character_name_map = {}
            self.weapon_name_map = {}

        return self.character_name_map, self.weapon_name_map

    def convert_combo_to_character_names(self, combo_value):
        character_name_map, weapon_name_map = self.load_master_name_maps()
        if not combo_value or '|' not in str(combo_value):
            return combo_value

        character_part, weapon_part = str(combo_value).split('|', 1)
        character_names = []
        for character_num in character_part.split('_'):
            try:
                character_num_int = int(float(character_num))
                character_names.append(character_name_map.get(character_num_int, character_num))
            except ValueError:
                character_names.append(character_num)

        weapon_names = []
        for weapon_code in weapon_part.split('_'):
            try:
                weapon_code_int = int(float(weapon_code))
                weapon_names.append(weapon_name_map.get(weapon_code_int, weapon_code))
            except ValueError:
                weapon_names.append(weapon_code)

        return f"{'_'.join(character_names)}|{'_'.join(weapon_names)}"

    def add_combo_columns(self, df):
        df = df.copy()
        df['character_combo'] = df[
            ['characterNum_1', 'characterNum_2', 'characterNum_3']
        ].apply(lambda row: '_'.join(map(str, sorted(row.tolist()))), axis=1).astype(str)
        df['weapon_combo'] = df[
            ['weaponCode_1', 'weaponCode_2', 'weaponCode_3']
        ].apply(lambda row: '_'.join(map(str, sorted(row.tolist()))), axis=1).astype(str)
        df['combo'] = df['character_combo'].astype(str) + '|' + df['weapon_combo'].astype(str)
        return df

    def build_character_getmmr_map(self, train_df, ranktier_threshold=6000):
        high_rank_df = train_df[train_df['avg_ranktier'] >= ranktier_threshold].copy()

        character_mmr_long = high_rank_df.melt(
            id_vars=['avg_getmmr'],
            value_vars=['characterNum_1', 'characterNum_2', 'characterNum_3'],
            var_name='character_slot',
            value_name='characterNum',
        ).dropna(subset=['characterNum', 'avg_getmmr'])

        return (
            character_mmr_long.groupby('characterNum')['avg_getmmr']
            .mean()
            .to_dict()
        )

    def apply_character_getmmr_map(self, df, character_mmr_map):
        df = df.copy()
        for col in ['characterNum_1', 'characterNum_2', 'characterNum_3']:
            df[f'{col}_avg_getmmr'] = df[col].map(character_mmr_map)
        return df

    def build_character_synergy_map(self, train_df, target_col='avg_getmmr'):
        pair_rows = []
        for _, row in train_df[['characterNum_1', 'characterNum_2', 'characterNum_3', target_col]].dropna().iterrows():
            characters = sorted([row['characterNum_1'], row['characterNum_2'], row['characterNum_3']])
            pair_rows.extend([
                {'pair_key': f'{characters[0]}_{characters[1]}', target_col: row[target_col]},
                {'pair_key': f'{characters[0]}_{characters[2]}', target_col: row[target_col]},
                {'pair_key': f'{characters[1]}_{characters[2]}', target_col: row[target_col]},
            ])

        pair_df = pd.DataFrame(pair_rows)
        if pair_df.empty:
            return {}

        return pair_df.groupby('pair_key')[target_col].mean().to_dict()

    def apply_character_synergy_map(self, df, synergy_map):
        df = df.copy()

        def build_pair_keys(row):
            characters = sorted([row['characterNum_1'], row['characterNum_2'], row['characterNum_3']])
            return (
                f'{characters[0]}_{characters[1]}',
                f'{characters[0]}_{characters[2]}',
                f'{characters[1]}_{characters[2]}',
            )

        pair_keys = df.apply(build_pair_keys, axis=1, result_type='expand')
        pair_keys.columns = ['pair_key_1', 'pair_key_2', 'pair_key_3']
        df = pd.concat([df, pair_keys], axis=1)

        df['character_synergy_1'] = df['pair_key_1'].map(synergy_map)
        df['character_synergy_2'] = df['pair_key_2'].map(synergy_map)
        df['character_synergy_3'] = df['pair_key_3'].map(synergy_map)
        df['character_synergy_mean'] = df[
            ['character_synergy_1', 'character_synergy_2', 'character_synergy_3']
        ].mean(axis=1)

        return df.drop(columns=['pair_key_1', 'pair_key_2', 'pair_key_3'], errors='ignore')

    def transform_target(self, y, target_col):
        y = pd.Series(y).astype(float)
        if target_col == 'avg_getmmr':
            return y
        return np.log1p(y)

    def inverse_transform_target(self, y, target_col):
        y = pd.Series(y).astype(float)
        if target_col == 'avg_getmmr':
            return y
        return np.expm1(y)

    def find_datetime_column(self, df):
        for col in ['startDtm', 'startdtm', 'start_dtm']:
            if col in df.columns:
                return col
        return None

    def filter_before_datetime(self, df, cutoff_datetime):
        datetime_col = self.find_datetime_column(df)
        if datetime_col is None or cutoff_datetime is None or str(cutoff_datetime).strip() == '':
            return df

        cutoff = pd.Timestamp(cutoff_datetime)
        event_time = pd.to_datetime(df[datetime_col], errors='coerce')
        return df[event_time < cutoff].copy()

    def build_time_decay_weights(self, df, reference_datetime='2026-04-16', half_life_days=7, min_weight=0.01):
        datetime_col = self.find_datetime_column(df)
        if datetime_col is None:
            return pd.Series(1.0, index=df.index)

        reference_time = pd.Timestamp(reference_datetime)
        event_time = pd.to_datetime(df[datetime_col], errors='coerce')
        age_days = (reference_time - event_time).dt.total_seconds() / (60 * 60 * 24)
        age_days = age_days.clip(lower=0).fillna(age_days.max())

        # 기준일에서 1주일 멀어질 때마다 영향력이 절반으로 줄어듭니다.
        weights = np.power(0.5, age_days / half_life_days)
        weights = pd.Series(weights, index=df.index).fillna(min_weight).clip(lower=min_weight, upper=1.0)
        return weights

    def prepare_recency_adjusted_df(
        self,
        df,
        recent_days=7,
        medium_days=14,
        recent_weight=1.0,
        medium_weight=0.7,
        old_weight=0.5,
        rankpoint_threshold=6200,
        random_state=42,
    ):
        datetime_col = self.find_datetime_column(df)
        prepared_df = df.copy()
        if datetime_col is None:
            prepared_df['_sample_weight'] = 1.0
            prepared_df['_recency_bucket'] = 'unknown'
            return prepared_df

        event_time = pd.to_datetime(prepared_df[datetime_col], errors='coerce')
        latest_time = event_time.max()
        if pd.isna(latest_time):
            prepared_df['_sample_weight'] = 1.0
            prepared_df['_recency_bucket'] = 'unknown'
            return prepared_df

        if 'avg_rankpoint' not in prepared_df.columns:
            prepared_df['_sample_weight'] = 1.0
            prepared_df['_recency_bucket'] = 'missing_avg_rankpoint'
            return prepared_df

        age_days = ((latest_time - event_time).dt.total_seconds() / (60 * 60 * 24)).clip(lower=0)
        prepared_df['_age_days'] = age_days

        lower_rankpoint_df = prepared_df[prepared_df['avg_rankpoint'] < rankpoint_threshold].copy()
        target_df = prepared_df[prepared_df['avg_rankpoint'] >= rankpoint_threshold].copy()

        if target_df.empty:
            lower_rankpoint_df['_sample_weight'] = 1.0
            lower_rankpoint_df['_recency_bucket'] = 'below_6000'
            return lower_rankpoint_df.reset_index(drop=True)

        recent_df = target_df[target_df['_age_days'] <= recent_days].copy()
        medium_df = target_df[
            (target_df['_age_days'] > recent_days) & (target_df['_age_days'] <= medium_days)
        ].copy()
        old_df = target_df[target_df['_age_days'] > medium_days].copy()

        recent_df['_sample_weight'] = recent_weight
        recent_df['_recency_bucket'] = 'recent_7d'
        medium_df['_sample_weight'] = medium_weight
        medium_df['_recency_bucket'] = 'medium_14d'
        old_df['_sample_weight'] = old_weight
        old_df['_recency_bucket'] = 'old_over_14d'
        lower_rankpoint_df['_sample_weight'] = 1.0
        lower_rankpoint_df['_recency_bucket'] = 'below_6000'

        bucket_sizes = [len(recent_df), len(medium_df)]
        bucket_sizes = [size for size in bucket_sizes if size > 0]
        target_old_count = int(round(np.mean(bucket_sizes))) if bucket_sizes else len(old_df)

        if len(old_df) > target_old_count > 0:
            old_df = old_df.sample(n=target_old_count, random_state=random_state)

        adjusted_df = pd.concat([lower_rankpoint_df, recent_df, medium_df, old_df], ignore_index=False)
        adjusted_df = adjusted_df.sample(frac=1.0, random_state=random_state).reset_index(drop=True)
        return adjusted_df

    def summarize_recency_buckets(self, df, recent_days=7, medium_days=14, rankpoint_threshold=6000):
        summary = {
            'total_rows': len(df),
            'above_6000_rows': None,
            'below_6000_rows': None,
            'recent_7d_rows': None,
            'medium_14d_rows': None,
            'old_over_14d_rows': None,
        }

        if 'avg_rankpoint' not in df.columns:
            return summary

        summary['above_6000_rows'] = int((df['avg_rankpoint'] >= rankpoint_threshold).sum())
        summary['below_6000_rows'] = int((df['avg_rankpoint'] < rankpoint_threshold).sum())

        datetime_col = self.find_datetime_column(df)
        if datetime_col is None:
            return summary

        event_time = pd.to_datetime(df[datetime_col], errors='coerce')
        latest_time = event_time.max()
        if pd.isna(latest_time):
            return summary

        age_days = ((latest_time - event_time).dt.total_seconds() / (60 * 60 * 24)).clip(lower=0)
        target_mask = df['avg_rankpoint'] >= rankpoint_threshold
        summary['recent_7d_rows'] = int((target_mask & (age_days <= recent_days)).sum())
        summary['medium_14d_rows'] = int((target_mask & (age_days > recent_days) & (age_days <= medium_days)).sum())
        summary['old_over_14d_rows'] = int((target_mask & (age_days > medium_days)).sum())
        return summary

    def split_df_by_tier_group(self):
        if self.df is None or self.df.empty:
            raise ValueError("DataFrame is empty. Run conect_db() first.")

        # 학습에 직접 쓰지 않을 메타 정보 컬럼 제거
        drop_columns = ['gameid', 'gamerank', 'matchingmode', 'teamNumber']
        # avg_ranktier를 기준으로 3개 구간 라벨(0, 1, 2) 생성
        tier_bins = [-np.inf, 4000, 6000, np.inf]
        tier_labels = [
            0,
            1,
            2
        ]

        self.df['tier_group'] = pd.cut(
            self.df['avg_ranktier'],
            bins=tier_bins,
            labels=tier_labels,
            right=False,
        )

        # 티어 그룹별로 분리된 학습용 DataFrame 저장
        self.tier_group_dfs = {
            tier: group_df.drop(columns=drop_columns, errors='ignore').reset_index(drop=True)
            for tier, group_df in self.df.groupby('tier_group', observed=False)
            if not group_df.empty
        }

        return self.tier_group_dfs

    def train_xgb_by_tier_group(
        self,
        target_col='avg_getmmr',
        test_size=0.3,
        random_state=42,
        target_tier=None,
        use_time_decay=True,
        cutoff_datetime=None,
        recent_days=7,
        medium_days=14,
        recent_weight=1.0,
        medium_weight=0.5,
        old_weight=0.2,
        rankpoint_threshold=6200,
        model_params=None,
    ):
        if not self.tier_group_dfs:
            raise ValueError("Tier grouped DataFrames are empty. Run split_df_by_tier_group() first.")

        self.tier_models = {}
        self.tier_results = {}
        self.tier_feature_columns = {}
        self.tier_label_encoders = {}
        self.tier_prediction_samples = {}

        # target_tier가 없으면 전체 티어를 합쳐 학습하고, 있으면 해당 티어만 사용
        if target_tier is None:
            selected_tiers = {'all_tiers': pd.concat(self.tier_group_dfs.values(), ignore_index=True)}
        else:
            selected_tiers = {target_tier: self.tier_group_dfs[target_tier]} if target_tier in self.tier_group_dfs else {}

        for tier, tier_df in selected_tiers.items():
            if target_col not in tier_df.columns:
                print(f"Tier {tier}: target column '{target_col}' not found.")
                continue

            raw_summary = self.summarize_recency_buckets(
                tier_df,
                recent_days=recent_days,
                medium_days=medium_days,
                rankpoint_threshold=rankpoint_threshold,
            )
            print(
                f"Tier {tier} raw rows: total={raw_summary['total_rows']}, "
                f"above_threshold={raw_summary['above_6000_rows']}, below_threshold={raw_summary['below_6000_rows']}, "
                f"recent_7d={raw_summary['recent_7d_rows']}, medium_14d={raw_summary['medium_14d_rows']}, "
                f"old_over_14d={raw_summary['old_over_14d_rows']}"
            )

            tier_df = self.filter_before_datetime(tier_df, cutoff_datetime)
            filtered_summary = self.summarize_recency_buckets(
                tier_df,
                recent_days=recent_days,
                medium_days=medium_days,
                rankpoint_threshold=rankpoint_threshold,
            )
            print(
                f"Tier {tier} after cutoff: total={filtered_summary['total_rows']}, "
                f"above_threshold={filtered_summary['above_6000_rows']}, below_threshold={filtered_summary['below_6000_rows']}, "
                f"recent_7d={filtered_summary['recent_7d_rows']}, medium_14d={filtered_summary['medium_14d_rows']}, "
                f"old_over_14d={filtered_summary['old_over_14d_rows']}"
            )

            tier_df = self.prepare_recency_adjusted_df(
                tier_df.dropna(subset=[target_col]).copy(),
                recent_days=recent_days,
                medium_days=medium_days,
                recent_weight=recent_weight,
                medium_weight=medium_weight,
                old_weight=old_weight,
                rankpoint_threshold=rankpoint_threshold,
                random_state=random_state,
            )
            adjusted_bucket_counts = (
                tier_df['_recency_bucket'].value_counts(dropna=False).to_dict()
                if '_recency_bucket' in tier_df.columns
                else {}
            )
            print(f"Tier {tier} after recency adjustment: rows={len(tier_df)}, buckets={adjusted_bucket_counts}")

            model_df = self.add_combo_columns(tier_df)
            if len(model_df) < 10:
                print(f"Tier {tier}: not enough rows to train ({len(model_df)} rows).")
                continue

            groups = model_df['combo']
            y_all = self.transform_target(model_df[target_col], target_col)

            # 1) 먼저 combo 기준으로 train/test 분할
            outer_splitter = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=random_state)
            train_full_idx, test_idx = next(outer_splitter.split(model_df, y_all, groups=groups))

            train_full_df = model_df.iloc[train_full_idx].copy()
            test_df = model_df.iloc[test_idx].copy()
            groups_train_full = train_full_df['combo']
            print(
                f"Tier {tier} split 1: train_full={len(train_full_df)}, test={len(test_df)}, "
                f"train_full_combos={train_full_df['combo'].nunique()}, test_combos={test_df['combo'].nunique()}"
            )

            # 2) train 안에서만 combo 기준으로 train/valid 분할
            inner_splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=random_state)
            train_idx, valid_idx = next(
                inner_splitter.split(
                    train_full_df,
                    self.transform_target(train_full_df[target_col], target_col),
                    groups=groups_train_full
                )
            )

            train_df = train_full_df.iloc[train_idx].copy()
            valid_df = train_full_df.iloc[valid_idx].copy()
            print(
                f"Tier {tier} split 2: train={len(train_df)}, valid={len(valid_df)}, "
                f"train_combos={train_df['combo'].nunique()}, valid_combos={valid_df['combo'].nunique()}"
            )

            # 3) train 데이터만 가지고 캐릭터 통계맵 생성
            character_mmr_map = self.build_character_getmmr_map(train_df)
            character_synergy_map = self.build_character_synergy_map(train_df, target_col=target_col)

            # 4) 같은 train 통계맵을 train/valid/test에 붙임
            train_df = self.apply_character_getmmr_map(train_df, character_mmr_map)
            valid_df = self.apply_character_getmmr_map(valid_df, character_mmr_map)
            test_df = self.apply_character_getmmr_map(test_df, character_mmr_map)
            train_df = self.apply_character_synergy_map(train_df, character_synergy_map)
            valid_df = self.apply_character_synergy_map(valid_df, character_synergy_map)
            test_df = self.apply_character_synergy_map(test_df, character_synergy_map)

            feature_columns = [
                'characterNum_1_avg_getmmr',
                'characterNum_2_avg_getmmr',
                'characterNum_3_avg_getmmr',
                'character_synergy_1',
                'character_synergy_2',
                'character_synergy_3',
                'character_synergy_mean',
                'character_avg_mmrgain_1',
                'character_avg_mmrgain_2',
                'character_avg_mmrgain_3',
                'team_character_avg_mmrgain',
                'highest_mmr_character',
                'highest_mmr_position_main',
                'highest_mmr_position_sub',
                'highest_mmr_player_1',
                'highest_mmr_player_2',
                'highest_mmr_player_3',
                'characterNum_1', 'characterNum_2', 'characterNum_3',
                'weaponCode_1', 'weaponCode_2', 'weaponCode_3',
                'position_main_1', 'position_main_2', 'position_main_3',
                'position_sub_1', 'position_sub_2', 'position_sub_3',
                'healAmount_1', 'healAmount_2', 'healAmount_3',
                'total_healAmount', 'avg_healAmount',
                'damage_std',
                'main_melee_cnt', 'main_ranged_cnt', 'main_support_cnt',
                'sub_bruiser_cnt', 'sub_assassin_cnt', 'sub_poke_cnt',
                'sub_sustain_cnt', 'sub_util_cnt', 'sub_tank_cnt', 'sub_nuker_cnt',
            ]
            available_features = [col for col in feature_columns if col in train_df.columns]
            X_train = train_df[available_features].copy()
            X_valid = valid_df[available_features].copy()
            X_test = test_df[available_features].copy()

            # 5) 라벨 인코딩도 train 기준으로만 fitting
            label_encoders = {}
            categorical_columns = X_train.select_dtypes(include=['object', 'category']).columns
            for col in categorical_columns:
                train_values = X_train[col].astype(str).fillna('MISSING')
                valid_values = X_valid[col].astype(str).fillna('MISSING')
                test_values = X_test[col].astype(str).fillna('MISSING')

                unique_values = sorted(train_values.unique().tolist())
                label_encoders[col] = {value: idx for idx, value in enumerate(unique_values)}

                X_train[col] = train_values.map(label_encoders[col]).fillna(-1).astype('int64')
                X_valid[col] = valid_values.map(label_encoders[col]).fillna(-1).astype('int64')
                X_test[col] = test_values.map(label_encoders[col]).fillna(-1).astype('int64')

            self.tier_feature_columns[tier] = X_train.columns.tolist()
            self.tier_label_encoders[tier] = label_encoders

            y_train = self.transform_target(train_df[target_col], target_col)
            y_valid = self.transform_target(valid_df[target_col], target_col)
            y_test = self.transform_target(test_df[target_col], target_col)
            train_weights = (
                train_df['_sample_weight'].astype(float).reset_index(drop=True)
                if use_time_decay
                else pd.Series(1.0, index=train_df.index)
            )
            valid_weights = (
                valid_df['_sample_weight'].astype(float).reset_index(drop=True)
                if use_time_decay
                else pd.Series(1.0, index=valid_df.index)
            )

            # 회귀용 XGBoost 모델
            base_model_params = {
                'objective': 'reg:squarederror',
                'n_estimators': 500000,
                'learning_rate': 0.002,
                'max_depth': 5,
                'min_child_weight': 10,
                'reg_alpha': 0.5,
                'reg_lambda': 2,
                'subsample': 0.8,
                'colsample_bytree': 0.8,
                'random_state': random_state,
                'early_stopping_rounds': 30,
                'device': 'cuda',
            }
            if model_params:
                base_model_params.update(model_params)

            model = XGBRegressor(**base_model_params)

            model.fit(
                X_train,
                y_train,
                sample_weight=train_weights,
                eval_set=[(X_valid, y_valid)],
                sample_weight_eval_set=[valid_weights],
                verbose=False,
            )

            y_pred_log = model.predict(X_test)
            y_test_original = self.inverse_transform_target(y_test, target_col)
            y_pred_original = self.inverse_transform_target(y_pred_log, target_col)

            # 티어별 모델과 평가 결과를 보관
            self.tier_models[tier] = model
            self.tier_prediction_samples[tier] = pd.DataFrame({
                'combo': test_df['combo'].reset_index(drop=True),
                f'actual_{target_col}': y_test_original.reset_index(drop=True),
                f'predicted_{target_col}': pd.Series(y_pred_original),
            }).assign(
                combo_character_names=lambda df: df['combo'].apply(self.convert_combo_to_character_names),
                abs_error=lambda df: (df[f'actual_{target_col}'] - df[f'predicted_{target_col}']).abs()
            )
            self.tier_results[tier] = {
                'rows': len(model_df),
                'below_6000_rows': int((model_df['_recency_bucket'] == 'below_6000').sum()) if '_recency_bucket' in model_df.columns else None,
                'recent_rows': int((model_df['_recency_bucket'] == 'recent_7d').sum()) if '_recency_bucket' in model_df.columns else None,
                'medium_rows': int((model_df['_recency_bucket'] == 'medium_14d').sum()) if '_recency_bucket' in model_df.columns else None,
                'old_rows': int((model_df['_recency_bucket'] == 'old_over_14d').sum()) if '_recency_bucket' in model_df.columns else None,
                'train_rows': len(X_train),
                'valid_rows': len(X_valid),
                'test_rows': len(X_test),
                'time_decay': use_time_decay,
                'cutoff_datetime': cutoff_datetime,
                'recent_days': recent_days if use_time_decay else None,
                'medium_days': medium_days if use_time_decay else None,
                'recent_weight': recent_weight if use_time_decay else None,
                'medium_weight': medium_weight if use_time_decay else None,
                'old_weight': old_weight if use_time_decay else None,
                'rankpoint_threshold': rankpoint_threshold if use_time_decay else None,
                'train_weight_mean': float(train_weights.mean()),
                'train_weight_min': float(train_weights.min()),
                'mae': mean_absolute_error(y_test_original, y_pred_original),
                'rmse': root_mean_squared_error(y_test_original, y_pred_original),
                'r2': r2_score(y_test_original, y_pred_original),
            }

        return pd.DataFrame(self.tier_results).T.sort_index()

    def print_prediction_samples(self, n=10):
        if not self.tier_prediction_samples:
            raise ValueError("No prediction samples found. Run train_xgb_by_tier_group() first.")

        for tier, sample_df in self.tier_prediction_samples.items():
            print(f"\nPrediction samples for {tier} (top {n})")
            print(sample_df.head(n).to_string(index=False))

    def save_models(self, save_dir='eternareturn_DB/models', file_suffix=''):
        if not self.tier_models:
            raise ValueError("No trained models found. Run train_xgb_by_tier_group() first.")

        os.makedirs(save_dir, exist_ok=True)

        for tier, model in self.tier_models.items():
            suffix = f'_{file_suffix}' if file_suffix else ''
            model_path = os.path.join(save_dir, f'xgb_model_{tier}{suffix}.json')
            feature_path = os.path.join(save_dir, f'xgb_model_{tier}{suffix}_features.csv')
            encoder_path = os.path.join(save_dir, f'xgb_model_{tier}{suffix}_label_encoders.json')

            model.save_model(model_path)
            pd.Series(self.tier_feature_columns.get(tier, []), name='feature_name').to_csv(
                feature_path, index=False
            )
            with open(encoder_path, 'w', encoding='utf-8') as f:
                json.dump(self.tier_label_encoders.get(tier, {}), f, ensure_ascii=False, indent=2)

        print(f"Models saved to: {os.path.abspath(save_dir)}")
            
    def histogram(self):
        plt.figure(figsize=(10, 6))
        sns.histplot(self.df['avg_ranktier'], bins=50, kde=True)
        plt.title('Distribution of Ranks')
        plt.xlabel('Rank')
        plt.show()

if __name__ == "__main__":
    er_db = ERDBClassification()
    er_db.conect_db()
    er_db.split_df_by_tier_group()
    results_df = er_db.train_xgb_by_tier_group()
    print(results_df)
    if not results_df.empty and er_db.tier_prediction_samples:
        er_db.print_prediction_samples(10)
    else:
        print("No prediction samples were generated. Check filters or training row counts.")

    if not results_df.empty and er_db.tier_models:
        er_db.save_models()
    else:
        print("No trained models were generated, so model saving was skipped.")
