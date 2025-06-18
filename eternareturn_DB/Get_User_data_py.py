import requests
import fastapi
import sqlite3
import json
import pandas as pd
import numpy as np
from collections import defaultdict
class send_erdata():

    def __init__(self):
        self.test_id="43543072"
        self.file_path=r"C:\Users\RodRic\Documents\GitHub\ER_search_character\eternareturn_DB\api_key\api_key.txt"
        self.api_link=r"https://open-api.bser.io/v1/games/"
        self.teams=None
        self.rawdata=None
        print(self.api_link)


    def read_api_key(self):
        try:
            with open(self.file_path, 'r', encoding='utf-8') as file:
                key = file.read()
                print(key)
        except FileNotFoundError:
            return print(f"파일을 찾을 수 없습니다: {self.file_path}")
        except Exception as e:
             return print(f"파일 읽기 중 오류 발생: {e}")
        headers = {
            "x-api-key": key
        }
        try:
            response=requests.get(self.api_link,headers=headers)
            response.raise_for_status()  # HTTP 오류 발생 시 예외 처리
            self.rawdata = response.json()
            print(self.rawdata)
        except requests.RequestException as e:
            print("요청 중 오류 발생:", e)
        self.teams  = defaultdict(list)
        for game in self.rawdata.get("userGames", []):
            team = game.get("gameRank")
            self.teams[team].append({
                "gameId":       game.get("gameId"),
                "nickname":     game.get("nickname", None),
                "rankTier":     game.get("mmrBefore", None),
                "getRP":        game.get("mmrGain", None),
                "characterNum": game.get("characterNum", None),
            })
        # 각 팀별로 개별 플레이어 통계 출력
        for team_rank, players in self.teams.items():
            print(f"팀 (게임 랭크 = {team_rank}):")
            for player in enumerate(players):
                print(f"    캐릭터: {player['characterNum']}")
                print(f"    획득RP: {player['getRP']}")
            print()

    def send_db(self):
        path="./db/db.db"
        with sqlite3.connect(path) as condb:
            conn=sqlite3.connect(path)
