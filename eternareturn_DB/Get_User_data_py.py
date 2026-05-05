import gc
import json
import os
import time
from datetime import datetime, timedelta

import pandas as pd
import pymysql
import requests
from dotenv import load_dotenv

load_dotenv()


BATTLE_USER_RESULT_FIELD_SPECS = [
    ("nickname", "str"),
    ("matchingTeamMode", "int"),
    ("seasonId", "int"),
    ("characterNum", "int"),
    ("skinCode", "int"),
    ("characterLevel", "int"),
    ("playerKill", "int"),
    ("playerAssistant", "int"),
    ("monsterKill", "int"),
    ("bestWeapon", "int"),
    ("bestWeaponLevel", "int"),
    ("masteryLevel", "json"),
    ("equipment", "json"),
    ("versionSeason", "int"),
    ("versionMajor", "int"),
    ("versionMinor", "int"),
    ("language", "str"),
    ("skillLevelInfo", "json"),
    ("skillOrderInfo", "json"),
    ("serverName", "str"),
    ("maxHp", "int"),
    ("maxSp", "int"),
    ("attackPower", "int"),
    ("moveSpeed", "float"),
    ("defense", "int"),
    ("hpRegen", "float"),
    ("spRegen", "float"),
    ("attackSpeed", "float"),
    ("outOfCombatMoveSpeed", "float"),
    ("sightRange", "float"),
    ("attackRange", "float"),
    ("criticalStrikeChance", "float"),
    ("criticalStrikeDamage", "float"),
    ("coolDownReduction", "float"),
    ("lifeSteal", "float"),
    ("normalLifeSteal", "float"),
    ("skillLifeSteal", "float"),
    ("amplifierToMonster", "float"),
    ("trapDamage", "float"),
    ("gainExp", "int"),
    ("mmrBefore", "int"),
    ("mmrGain", "int"),
    ("mmrAfter", "int"),
    ("playTime", "int"),
    ("watchTime", "int"),
    ("totalTime", "int"),
    ("botAdded", "int"),
    ("botRemain", "int"),
    ("restrictedAreaAccelerated", "int"),
    ("safeAreas", "int"),
    ("teamNumber", "int"),
    ("preMade", "int"),
    ("eventMissionResult", "json"),
    ("gainedNormalMmrKFactor", "float"),
    ("victory", "bool"),
    ("craftUncommon", "int"),
    ("craftRare", "int"),
    ("craftEpic", "int"),
    ("craftLegend", "int"),
    ("damageToPlayer", "int"),
    ("damageToPlayer_trap", "int"),
    ("damageToPlayer_basic", "int"),
    ("damageToPlayer_skill", "int"),
    ("damageToPlayer_itemSkill", "int"),
    ("damageToPlayer_direct", "int"),
    ("damageToPlayer_uniqueSkill", "int"),
    ("damageFromPlayer", "int"),
    ("damageFromPlayer_trap", "int"),
    ("damageFromPlayer_basic", "int"),
    ("damageFromPlayer_skill", "int"),
    ("damageFromPlayer_itemSkill", "int"),
    ("damageFromPlayer_direct", "int"),
    ("damageFromPlayer_uniqueSkill", "int"),
    ("damageToMonster", "int"),
    ("damageToMonster_trap", "int"),
    ("damageToMonster_basic", "int"),
    ("damageToMonster_skill", "int"),
    ("damageToMonster_itemSkill", "int"),
    ("damageToMonster_direct", "int"),
    ("damageToMonster_uniqueSkill", "int"),
    ("damageFromMonster", "int"),
    ("damageToPlayer_Shield", "int"),
    ("damageOffsetedByShield_Player", "int"),
    ("damageOffsetedByShield_Monster", "int"),
    ("killMonsters", "json"),
    ("healAmount", "int"),
    ("teamRecover", "int"),
    ("protectAbsorb", "int"),
    ("addSurveillanceCamera", "int"),
    ("addTelephotoCamera", "int"),
    ("removeSurveillanceCamera", "int"),
    ("removeTelephotoCamera", "int"),
    ("useHyperLoop", "int"),
    ("useSecurityConsole", "int"),
    ("giveUp", "bool"),
    ("teamSpectator", "bool"),
    ("routeIdOfStart", "int"),
    ("routeSlotId", "int"),
    ("placeOfStart", "int"),
    ("mmrAvg", "int"),
    ("teamKill", "int"),
    ("accountLevel", "int"),
    ("killerUserNum", "int"),
    ("killer", "str"),
    ("killDetail", "str"),
    ("killerCharacter", "str"),
    ("killerWeapon", "str"),
    ("causeOfDeath", "str"),
    ("placeOfDeath", "str"),
    ("fishingCount", "int"),
    ("useEmoticonCount", "int"),
    ("traitFirstCore", "int"),
    ("traitFirstSub", "json"),
    ("traitSecondSub", "json"),
    ("totalVFCredit", "json"),
    ("creditSource", "json"),
    ("usedVFCredit", "json"),
    ("itemTransferredConsole", "json"),
    ("itemTransferredDrone", "json"),
    ("craftMythic", "int"),
    ("playerDeaths", "int"),
    ("killGamma", "bool"),
    ("killDetails", "json"),
    ("deathDetails", "json"),
    ("ccTimeToPlayer", "float"),
    ("foodCraftCount", "json"),
    ("beverageCraftCount", "json"),
    ("airSupplyOpenCount", "json"),
    ("escapeState", "int"),
    ("collectItemForLog", "json"),
    ("equipFirstItemForLog", "json"),
    ("totalDoubleKill", "int"),
    ("totalTripleKill", "int"),
    ("totalQuadraKill", "int"),
    ("totalExtraKill", "int"),
    ("tacticalSkillGroup", "int"),
    ("tacticalSkillLevel", "int"),
    ("totalGainVFCredit", "int"),
    ("killPlayerGainVFCredit", "int"),
    ("killChickenGainVFCredit", "int"),
    ("killBoarGainVFCredit", "int"),
    ("killWildDogGainVFCredit", "int"),
    ("killWolfGainVFCredit", "int"),
    ("killBearGainVFCredit", "int"),
    ("killOmegaGainVFCredit", "int"),
    ("killBatGainVFCredit", "int"),
    ("killWicklineGainVFCredit", "int"),
    ("killAlphaGainVFCredit", "int"),
    ("killItemBountyGainVFCredit", "int"),
    ("killDroneGainVFCredit", "int"),
    ("killGammaGainVFCredit", "int"),
    ("killTurretGainVFCredit", "int"),
    ("itemShredderGainVFCredit", "int"),
    ("totalUseVFCredit", "int"),
    ("remoteDroneUseVFCreditMySelf", "int"),
    ("remoteDroneUseVFCreditAlly", "int"),
    ("transferConsoleFromMaterialUseVFCredit", "int"),
    ("transferConsoleFromEscapeKeyUseVFCredit", "int"),
    ("transferConsoleFromRevivalUseVFCredit", "int"),
    ("tacticalSkillUpgradeUseVFCredit", "int"),
    ("teamElimination", "int"),
    ("teamDown", "int"),
    ("teamBattleZoneDown", "int"),
    ("teamRepeatDown", "int"),
    ("adaptiveForce", "int"),
    ("adaptiveForceAttack", "int"),
    ("adaptiveForceAmplify", "int"),
    ("skillAmp", "int"),
    ("campFireCraftUncommon", "int"),
    ("campFireCraftRare", "int"),
    ("campFireCraftEpic", "int"),
    ("campFireCraftLegendary", "int"),
    ("tacticalSkillUseCount", "int"),
    ("creditRevivalCount", "int"),
    ("creditRevivedOthersCount", "int"),
    ("timeSpentInBriefingRoom", "int"),
    ("IsLeavingBeforeCreditRevivalTerminate", "bool"),
    ("crGetAnimal", "int"),
    ("crGetMutant", "int"),
    ("crGetPhaseStart", "int"),
    ("crGetKill", "int"),
    ("crGetAssist", "int"),
    ("crGetTimeElapsed", "int"),
    ("crGetCreditBonus", "int"),
    ("crUseRemoteDrone", "int"),
    ("crUseUpgradeTacticalSkill", "int"),
    ("crUseTreeOfLife", "int"),
    ("crUseMythril", "int"),
    ("crUseForceCore", "int"),
    ("crUseVFBloodSample", "int"),
    ("crUseRootkit", "int"),
    ("mmrGainInGame", "int"),
    ("mmrLossEntryCost", "int"),
    ("premadeMatchingType", "int"),
    ("viewContribution", "int"),
    ("useReconDrone", "int"),
    ("useEmpDrone", "int"),
    ("exceptPreMadeTeam", "int"),
    ("terminateCount", "int"),
    ("clutchCount", "int"),
    ("unknownKill", "int"),
    ("mainWeather", "int"),
    ("subWeather", "int"),
    ("activeInstallation", "json"),
    ("useGuideRobot", "int"),
    ("guideRobotRadial", "int"),
    ("guideRobotFlagShip", "int"),
    ("guideRobotSignature", "int"),
    ("crGetByGuideRobot", "int"),
    ("damageToGuideRobot", "int"),
    ("getBuffCubeRed", "int"),
    ("getBuffCubePurple", "int"),
    ("getBuffCubeGreen", "int"),
    ("getBuffCubeGold", "int"),
    ("getBuffCubeSkyBlue", "int"),
    ("sumGetBuffCube", "int"),
    ("teamDownCanNotEliminate", "int"),
    ("teamDownCanEliminate", "int"),
    ("teamRepeatDownCanNotEliminate", "int"),
    ("teamRepeatDownCanEliminate", "int"),
    ("enterDimensionRift", "int"),
    ("enterDimensionEmpoweredRift", "int"),
    ("winFromDimensionRift", "int"),
    ("winFromDimensionEmpoweredRift", "int"),
    ("enterTurbulentRift", "int"),
    ("useGadget", "json"),
    ("rankPoint", "int"),
]

PLAYER_WIDE_FIELDS = [field for field, _ in BATTLE_USER_RESULT_FIELD_SPECS]
NUMERIC_FIELDS = [field for field, kind in BATTLE_USER_RESULT_FIELD_SPECS if kind in {"int", "float", "bool"}]
RAW_JSON_FIELD = "battleUserResultRaw"
SQL_TYPE_MAP = {
    "int": "BIGINT",
    "float": "DOUBLE",
    "bool": "TINYINT(1)",
    "str": "TEXT",
    "json": "LONGTEXT",
}
class SendERData:
    def __init__(self, game_id: str, db_exist_mode: str = None):
        self.game_id = game_id
        self.teams = []
        self.summary_df = None
        self.wide_df = None
        self.player_df = None
        self.db_exist_mode = db_exist_mode
        self.http_session = requests.Session()
        self.mysql_config = {
            "host": os.getenv("DB_HOST"),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
            "database": os.getenv("DB_NAME"),
            "charset": "utf8mb4",
        }
        self.rank_table = "rankdb_v2"

    @property
    def api_url(self):
        return f"https://open-api.bser.io/v1/games/{self.game_id}"

    def get_mysql_conn(self):
        return pymysql.connect(
            host=self.mysql_config["host"],
            user=self.mysql_config["user"],
            password=self.mysql_config["password"],
            database=self.mysql_config["database"],
            charset=self.mysql_config["charset"],
            autocommit=True,
        )

    def get_table_columns(self, table_name):
        try:
            with self.get_mysql_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(f"SHOW COLUMNS FROM `{table_name}`")
                    return [row[0] for row in cur.fetchall()]
        except Exception as e:
            print(f"테이블 컬럼 조회 실패: {e}")
            return []

    def ensure_rankdb_v2_table(self):
        existing_columns = set(self.get_table_columns(self.rank_table))
        if existing_columns and (
            "player_slot" not in existing_columns
            or "avg_ranktier" in existing_columns
            or "avg_getmmr" in existing_columns
            or "avg_rankpoint" in existing_columns
        ):
            with self.get_mysql_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(f"DROP TABLE IF EXISTS `{self.rank_table}`")
                conn.commit()

        column_defs = [
            "`gameid` BIGINT NOT NULL",
            "`gamerank` INT NOT NULL",
            "`player_slot` INT NOT NULL",
            "`startDtm` DATETIME DEFAULT NULL",
            "`matchingmode` INT DEFAULT NULL",
        ]
        for field_name, field_kind in BATTLE_USER_RESULT_FIELD_SPECS:
            sql_type = SQL_TYPE_MAP[field_kind]
            column_defs.append(f"`{field_name}` {sql_type} DEFAULT NULL")
        create_sql = f"""
        CREATE TABLE IF NOT EXISTS `{self.rank_table}` (
            {", ".join(column_defs)},
            PRIMARY KEY (`gameid`, `gamerank`, `player_slot`)
        ) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
        """
        with self.get_mysql_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(create_sql)
            conn.commit()

    def clear_temp_data(self):
        self.teams = []
        self.summary_df = None
        self.wide_df = None
        self.player_df = None
        gc.collect()

    def first_db_check(self):
        print("데이터베이스 초기 상태 확인 중...")
        if not hasattr(self, "rank_table") or not self.rank_table:
            self.rank_table = "rankdb_v2"

        try:
            with self.get_mysql_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT COUNT(*)
                        FROM information_schema.tables
                        WHERE table_schema = %s
                        AND table_name = %s
                        """,
                        (self.mysql_config["database"], self.rank_table),
                    )
                    exists = cur.fetchone()[0]

                    if exists:
                        print(f"{self.rank_table} 테이블이 이미 존재합니다.")
                        self.db_exist_mode = "append"
                        cur.execute(f"SELECT MAX(gameid) FROM `{self.rank_table}`")
                        row = cur.fetchone()
                        max_gameid = row[0] if row and row[0] is not None else 0
                        print(f"현재 {self.rank_table}의 최대 gameid: {max_gameid}")
                    else:
                        print(f"{self.rank_table} 테이블이 없어 새로 생성합니다.")
                        self.ensure_rankdb_v2_table()
                        self.db_exist_mode = "replace"
        except Exception as e:
            print(f"DB 확인 중 오류 발생: {e}")

    def get_gameid_bound(self, mode="MAX"):
        try:
            with self.get_mysql_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(f"SELECT {mode}(gameid) FROM `{self.rank_table}`")
                    row = cur.fetchone()
                    return row[0] if row and row[0] is not None else 0
        except Exception as e:
            print(f"DB에서 {mode} gameid 조회 중 오류 발생: {e}")
            return None

    def get_max_gameid(self):
        return self.get_gameid_bound("MAX")

    def get_min_gameid(self):
        return self.get_gameid_bound("MIN")

    def put_game_id(self, game_id):
        self.game_id = game_id

    def convert_startdtm(self, value):
        if value is None:
            return None
        value = str(value)
        return value[:19].replace("T", " ")

    def is_older_than_hours(self, value, hours=2):
        converted = self.convert_startdtm(value)
        if converted is None:
            return False
        try:
            game_time = datetime.strptime(converted, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return False
        return game_time <= datetime.now() - timedelta(hours=hours)

    def is_before_datetime(self, value, cutoff_datetime):
        converted = self.convert_startdtm(value)
        if converted is None:
            return False
        try:
            game_time = datetime.strptime(converted, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return False

        if isinstance(cutoff_datetime, str):
            cutoff_dt = datetime.strptime(cutoff_datetime[:19].replace("T", " "), "%Y-%m-%d %H:%M:%S")
        else:
            cutoff_dt = cutoff_datetime
        return game_time < cutoff_dt

    def fetch_and_build(self):
        print("API 호출 중...")
        self.clear_temp_data()
        headers = {"x-api-key": os.getenv("API_KEY")}
        resp = self.http_session.get(self.api_url, headers=headers, timeout=10)

        if resp.status_code == 404:
            print(f"404 Not Found: {resp.url}")
            resp.close()
            return False

        data = resp.json()
        resp.close()
        if isinstance(data, dict) and data.get("code") == 404:
            print(f"Body code 404: {self.api_url}")
            return False

        self.teams = []
        for game in data.get("userGames", []):
            record = {
                "startDtm": game.get("startDtm"),
                "matchingmode": game.get("matchingMode"),
                "gamerank": game.get("gameRank"),
                "gameid": game.get("gameId"),
            }
            record[RAW_JSON_FIELD] = {field_name: game.get(field_name) for field_name, _ in BATTLE_USER_RESULT_FIELD_SPECS}
            for field_name, _ in BATTLE_USER_RESULT_FIELD_SPECS:
                record[field_name] = game.get(field_name)
            self.teams.append(record)

        df = pd.DataFrame(self.teams)
        print(f"API 호출 성공: {len(df)}개의 player result 로드")
        if df.empty:
            self.wide_df = pd.DataFrame()
            self.summary_df = pd.DataFrame()
            return False

        numeric_updates = {}
        for field_name in NUMERIC_FIELDS:
            if field_name in df.columns:
                numeric_updates[field_name] = pd.to_numeric(df[field_name], errors="coerce")

        df = df.assign(**numeric_updates).copy()
        df["player_slot"] = df.groupby(["gameid", "gamerank"]).cumcount() + 1

        player_cols = ["gameid", "gamerank", "startDtm", "matchingmode", "player_slot"] + PLAYER_WIDE_FIELDS
        self.player_df = df[player_cols].copy()
        self.summary_df = self.player_df.copy()
        self.wide_df = self.player_df.copy()

        del df, data
        gc.collect()
        print("player_df 생성 완료")
        return True

    def serialize_db_value(self, column_name, value):
        if column_name == "startDtm":
            return self.convert_startdtm(value)
        if value is None:
            return None
        if not isinstance(value, (list, dict, tuple)) and pd.isna(value):
            return None
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, (list, dict, tuple)):
            return json.dumps(value, ensure_ascii=False)
        if isinstance(value, pd.Timestamp):
            return value.to_pydatetime()
        return value

    def send_db(self, machingMode=None):
        print("데이터베이스 저장 중...")
        if self.wide_df is None and self.player_df is None:
            raise RuntimeError("데이터를 먼저 fetch_and_build()로 준비해주세요.")
        if getattr(self.wide_df, "empty", True) and getattr(self.player_df, "empty", True):
            print("wide_df가 비어있어 저장을 건너뜁니다.")
            return

        if machingMode == 3:
            table_name = self.rank_table
            self.ensure_rankdb_v2_table()
            target_df = self.player_df.copy()
        elif machingMode == 2:
            print("normaldb 저장은 현재 비활성화되어 있습니다. rankdb_v2만 raw player row로 저장합니다.")
            return
        else:
            print("matchingMode가 2 또는 3이 아니므로 저장하지 않습니다.")
            return

        table_columns = self.get_table_columns(table_name)
        if not table_columns:
            print(f"{table_name} 컬럼을 읽지 못해 저장을 건너뜁니다.")
            return

        insert_columns = [col for col in target_df.columns if col in table_columns]
        priority_columns = ["gameid", "gamerank", "player_slot", "startDtm", "matchingmode"]
        ordered_columns = [col for col in priority_columns if col in insert_columns]
        ordered_columns.extend([col for col in insert_columns if col not in ordered_columns])
        insert_columns = ordered_columns

        update_columns = [col for col in insert_columns if col not in {"gameid", "gamerank", "player_slot"}]
        placeholders = ", ".join(["%s"] * len(insert_columns))
        insert_sql = f"""
        INSERT INTO `{table_name}` ({", ".join(f"`{col}`" for col in insert_columns)})
        VALUES ({placeholders})
        ON DUPLICATE KEY UPDATE
        {", ".join(f"`{col}` = VALUES(`{col}`)" for col in update_columns)}
        """

        try:
            rows = []
            for _, row in target_df.iterrows():
                rows.append(tuple(self.serialize_db_value(col, row.get(col)) for col in insert_columns))

            with self.get_mysql_conn() as conn:
                with conn.cursor() as cur:
                    cur.executemany(insert_sql, rows)
                conn.commit()

            print(f"데이터베이스 저장 완료: table={table_name}, rows={len(rows)}")
            if machingMode == 3:
                print(f"{self.rank_table}에 gameid {self.game_id} 저장 완료")
            elif machingMode == 2:
                print(f"normaldb에 gameid {self.game_id} 저장 완료")
        except Exception as e:
            print(f"DB 저장 중 오류 발생: {e}")
        finally:
            self.clear_temp_data()


if __name__ == "__main__":
    sender = SendERData(game_id="58444343")
    settingmmode = 1
    loop_mode = 1
    loop_count = 10000000

    sender.first_db_check()

    if settingmmode == 0:
        sender.db_exist_mode = "replace"
        ok = sender.fetch_and_build()
        if ok:
            df = sender.wide_df
            if df is not None and not df.empty:
                mode = int(df["matchingmode"].iloc[0])
                if mode == 3:
                    sender.send_db(machingMode=3)
                elif mode == 2:
                    sender.send_db(machingMode=2)
                else:
                    print(f"PASS(mode={mode}): gameid={sender.game_id} 저장하지 않음")
                    sender.clear_temp_data()

    elif settingmmode == 1:
        min_id = sender.get_min_gameid()
        max_id = sender.get_max_gameid()

        if min_id is None or max_id is None:
            print("DB에서 gameid 범위를 읽지 못했습니다.")
            raise SystemExit

        sender.db_exist_mode = "append"
        print(f"현재 DB의 최소 gameid: {min_id}")
        print(f"현재 DB의 최대 gameid: {max_id}")

        if loop_mode == 1:
            select_loop = range(max_id + 1, max_id + 1 + loop_count)
        elif loop_mode == 2:
            if min_id <= 1:
                print("최소 gameid가 1 이하라 이전 gameid 수집을 진행하지 않습니다.")
                raise SystemExit
            select_loop = range(min_id - 1, max(min_id - 1 - loop_count, 0), -1)
        else:
            print("loop_mode는 1 또는 2만 지원합니다.")
            raise SystemExit

        for gid in select_loop:
            sender.put_game_id(gid)
            ok = sender.fetch_and_build()
            if not ok:
                print(f"SKIP(404/empty): gameid={gid}")
                sender.clear_temp_data()
                continue

            df = sender.wide_df
            if df is None or df.empty:
                print(f"SKIP(empty df): gameid={gid}")
                sender.clear_temp_data()
                continue

            first_startdtm = df["startDtm"].iloc[0] if "startDtm" in df.columns else None
            if not sender.is_older_than_hours(first_startdtm, hours=2):
                print(f"STOP(startDtm newer than 2 hours): gameid={gid}, startDtm={first_startdtm}")
                sender.clear_temp_data()
                break

            mode = int(df["matchingmode"].iloc[0])
            if mode == 3:
                sender.send_db(machingMode=3)
            elif mode == 2:
                sender.send_db(machingMode=2)
            else:
                print(f"PASS(mode={mode}): gameid={gid} 저장하지 않음")
                sender.clear_temp_data()

            time.sleep(1)
