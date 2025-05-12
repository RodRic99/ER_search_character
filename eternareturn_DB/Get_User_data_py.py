import requests
import fastapi
import sqlite3
import json
import pandas as pd
import numpy as np
from collections import defaultdict
class send_erdata():

    def __init__(self):
        test_id="43543072"
        file_path=r"C:\Users\wnsgu\OneDrive\바탕 화면\eternareturn_DB\api_key\api_key.txt"
        api_link=r"https://open-api.bser.io/v1/games/"+test_id
        print(api_link)


    def read_api_key(self):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                key = file.read()
                print(key)
        except FileNotFoundError:
            return print(f"파일을 찾을 수 없습니다: {file_path}")
        except Exception as e:
             return print(f"파일 읽기 중 오류 발생: {e}")
        headers = {
            "x-api-key": key
        }
        try:
            response=requests.get(api_link,headers=headers)
            response.raise_for_status()  # HTTP 오류 발생 시 예외 처리
            rawdata = response.json()
            print(rawdata)
        except requests.RequestException as e:
            print("요청 중 오류 발생:", e)
        teams  = defaultdict(list)



    for game in rawdata.get("userGames", []):
        team = game.get("gameRank")
        teams[team].append({
            "gameid":game.get("gameId")
            "nickname": game.get("nickname",None),
            "ranktier": game.get("mmrBefore",None),
            "getRP": game.get("mmrGain",None),
            "characterNum": game.get("characterNum", None)
        })
    # 각 팀별로 개별 플레이어 통계 출력

    for team_rank, players in teams.items():
        print(f"팀 (게임 랭크 = {team_rank}):")
        for player in enumerate(players):
            print(f"    캐릭터: {player['characterNum']}")
            print(f"    획득RP: {player['getRP']}")
        print()

    def send_db(self):
        path="./db/db.db"
        with sqlite3.connect(path) as condb:
            conn=sqlite3.connect(path)
