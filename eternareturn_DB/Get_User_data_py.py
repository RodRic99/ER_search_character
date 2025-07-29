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
        for game in data.get("userGames", []):
            self.teams.append({
                "gamerank":     game.get("gameRank"),
                "gameid":       game.get("gameId"),
                "nickname":     game.get("nickname"),
                "ranktier":     game.get("mmrBefore"),
                "getrp":        game.get("mmrGain"),
                "playerkill":        game.get("playerKill"),
                "demage":       game.get("damageToPlayer"),
                "characterNum": game.get("characterNum"),
                "bestWeapon": game.get("bestWeapon"),
                "rankpoint":    game.get("rankPoint"),
            })
       
        # 3) DataFrame 생성
        df = pd.DataFrame(self.teams)
        
        # 4) 그룹 요약: ranktier/getrp는 평균, 나머지는 리스트
        self.summary_df = (
            df
            .groupby('gamerank', as_index=False)
            .agg({
                'gameid':       'first',
                'nickname':     str,
                'demage':       list,
                'characterNum': list,
                'rankpoint':    list,
                'ranktier':     'mean',
                'getrp':        'mean',
            })
            .rename(columns={
                'ranktier': 'avg_ranktier',
                'getrp':    'avg_getrp'
            })
        )
        print(self.summary_df)



    def send_db(self):
        if self.summary_df is None:
            raise RuntimeError("데이터를 먼저 fetch_and_build()로 준비해주세요.")

        # 디렉터리 체크(없으면 생성)
        import os
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.isdir(db_dir):
            os.makedirs(db_dir, exist_ok=True)

        # 5) DB에 한 번만 연결해서 to_sql
        try:
            with sqlite3.connect(self.db_path) as conn:
                self.summary_df.to_sql(
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
        user_id="47832485",
        api_key_path=r".\api_key\api_key.txt",
        db_path="./db/db.db"
    )
    sender.fetch_and_build()
    sender.send_db()
