import requests
import sqlite3
import json
import pandas as pd
from collections import defaultdict

class SendERData:

    def __init__(self, user_id: str, api_key_path: str, db_path: str):
        self.user_id      = user_id
        self.api_key_path = api_key_path
        self.api_url      = f"https://open-api.bser.io/v1/games/{user_id}"
        self.db_path      = db_path
        self.teams        = []      # list[dict]
        self.summary_df   = None    # pandas.DataFrame

    def _load_api_key(self) -> str:
        try:
            with open(self.api_key_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception as e:
            raise RuntimeError(f"API 키 로드 실패: {e}")

    def fetch_and_build(self):
        # 1) API 호출
        key = self._load_api_key()
        headers = {"x-api-key": key}
        resp = requests.get(self.api_url, headers=headers)
        resp.raise_for_status()
        data = resp.json()

        # 2) rawdata → list of dict
        self.teams = []  # 잔여분 방지
        for game in data.get("userGames", []):
            self.teams.append({
                "matchingmode":  game.get("matchingMode"),
                "gamerank":      game.get("gameRank"),
                "gameid":        game.get("gameId"),
                "nickname":      game.get("nickname"),
                "ranktier":      game.get("mmrBefore"),
                "getmmr":        game.get("mmrGain"),         # ← 이름 일관
                "playerkill":    game.get("playerKill"),
                "damage":        game.get("damageToPlayer"),  # ← 철자 통일(선택)
                "characterNum":  game.get("characterNum"),
                "bestWeapon":    game.get("bestWeapon"),
                "rankpoint":     game.get("rankPoint"),       # ← rankPoint 사용
            })
        

        # 3) DataFrame 생성
        df = pd.DataFrame(self.teams)
        # 숫자 보장
        num_cols = ["ranktier", "getmmr", "rankpoint", "playerkill", "damage", "characterNum"]
        for c in num_cols:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce")

        print("=== raw df ===")
        print(df.head())

        # 4) 게임ID+팀별 요약: 평균/리스트/최빈값
        def mode_or_first(s: pd.Series):
            m = s.mode()
            return m.iat[0] if len(m) else (s.iloc[0] if len(s) else None)

        grouped = (
            df.groupby(['gameid','gamerank'], as_index=False)
            .agg({
                'matchingmode':  mode_or_first,  # 팀 내 동일하면 최빈값
                'nickname':      list,           # 개별값은 리스트로 보존
                'characterNum':  list,
                'damage':        list,
                'playerkill':    list,
                'bestWeapon':    list,
                'ranktier':      'mean',         # 대표 평균
                'getmmr':        'mean',
                'rankpoint':     'mean',
            })
            .rename(columns={
                'ranktier':  'avg_ranktier',
                'getmmr':    'avg_getmmr',
                'rankpoint': 'avg_rankpoint'
            })
        )
        self.summary_df = grouped
        print("=== summary_df (per gameid,gamerank) ===")
        print(self.summary_df.head())

        # 5) 리스트 컬럼을 멤버별 열로 분리 (폭 형태) — 안정적: explode → pivot
        #   닉네임/캐릭/피해/킬/무기까지 멤버별 열 생성
        list_cols = ['nickname','characterNum','damage','playerkill','bestWeapon']
        long = grouped.explode(list_cols, ignore_index=True)
        long['member_idx'] = long.groupby(['gameid','gamerank']).cumcount() + 1

        wide = long.pivot(index=['gameid','gamerank'],
                        columns='member_idx',
                        values=list_cols).sort_index(axis=1, level=0)

        # 멀티인덱스 → 단일 컬럼명 예: nickname_1, characterNum_1 ...
        wide.columns = [f'{col}_{idx}' for col, idx in wide.columns]
        wide = wide.reset_index()

        # 요약(평균들/모드)과 병합해 한 테이블로도 활용 가능
        meta_cols = ['gameid','gamerank','matchingmode','avg_ranktier','avg_getmmr','avg_rankpoint']
        final = wide.merge(grouped[meta_cols], on=['gameid','gamerank'], how='left')

        self.wide_df = final
        print("=== wide_df (members split + meta) ===")
        print(self.wide_df.head())


    def send_db(self):
        if self.wide_df is None:
            raise RuntimeError("데이터를 먼저 fetch_and_build()로 준비해주세요.")

        # 디렉터리 체크(없으면 생성)
        import os
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.isdir(db_dir):
            os.makedirs(db_dir, exist_ok=True)

        # 5) DB에 한 번만 연결해서 to_sql
        try:
            with sqlite3.connect(self.db_path) as conn:
                self.wide_df.to_sql(
                    'userdb',
                    conn,
                    if_exists='append',
                    index=False
                )
                print("✅ 데이터베이스에 성공적으로 저장했습니다.")
        except Exception as e:
            print(f"❌ DB 저장 중 오류 발생: {e}")

if __name__ == "__main__":
    sender = SendERData(
        user_id="50240000",
        api_key_path=r".\api_key\api_key.txt",
        db_path="./db/db.db"
    )
    sender.fetch_and_build()
    sender.send_db()
