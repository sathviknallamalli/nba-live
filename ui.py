import requests
from bs4 import BeautifulSoup
import urllib.request
import json
from openai import OpenAI
import os
import time
import traceback
from tkinter import PhotoImage
import asyncio
from tkinter import ttk
import aiohttp
import threading
import tkinter as tk
from websocket import WebSocketApp
import requests
import websocket
import json
import threading
import time
import base64
import zlib
import json
import re
import json
from collections import defaultdict
from difflib import SequenceMatcher
import re
from dotenv import load_dotenv
from langchain_community.agent_toolkits.load_tools import load_tools
from langchain.agents import initialize_agent, Tool, create_react_agent, AgentExecutor
from langchain_openai import ChatOpenAI
from langchain.agents import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents.format_scratchpad.openai_tools import (
    format_to_openai_tool_messages,
)
from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser
from langchain.agents import AgentExecutor
from langchain_community.utilities import SerpAPIWrapper

load_dotenv()
open_ai_key = os.getenv("OPENAI_APIKEY")
serp_api_key = os.getenv("SERP_APIKEY")

openai_client = OpenAI(
  api_key=open_ai_key,
)

with open('./teams.json', 'r') as file:
    id_to_team = json.load(file)
# Global list to store incoming messages
incoming_messages = []
query_output = []
chat_messages = []

def process_play_by_play(play_data):
    key_moments = []

    for play in play_data:
        time = play['clock']['displayValue']
        description = play['text']
        
        # Check for scoring plays
        if 'makes' in description or 'misses' in description:
            key_moments.append({
                'time': time,
                'event': 'scoring',
                'description': description
            })
        # Check for fouls
        elif 'foul' in description:
            key_moments.append({
                'time': time,
                'event': 'foul',
                'description': description
            })
        # Check for turnovers
        elif 'turnover' in description:
            key_moments.append({
                'time': time,
                'event': 'turnover',
                'description': description
            })
        elif 'defensive rebound' in description:
            key_moments.append({
                'time': time,
                'event': 'defensive rebound',
                'description': description
            })
        elif 'offensive rebound' in description:
            key_moments.append({
                'time': time,
                'event': 'offensive rebound',
                'description': description
            })
        # Add more conditions as needed

    return key_moments
def generate_queries_with_gpt(key_moments, game_info):
    prompt = (
        f"We are watching a live NBA game between {game_info['team1']} and {game_info['team2']} on {game_info['date']}. "
        f"Here are the key moments from the game so far:\n\n"
    )

    for moment in key_moments:
        prompt += f"{moment['time']}: {moment['description']} (Event: {moment['event']})\n"

    prompt += (
        "\nBased on these key moments, please generate 3-5 stat-driven queries that focus on historical comparisons, "
        "team trends, and notable player achievements in past games. Avoid hypothetical or predictive questions. "
        "The queries should be actionable and reflect a broader understanding of NBA stats and trends. "
        "Include queries about the game so far and comparisons to prior games this season or previous seasons."
        "When referring to seasons, use the format '2021-22 season'."
        "Avoid 'how' based qualitative questions and generate quantificable queries that can be answered with statistical data."
        "Make the queries specific, avoid general trend comparisons. Specify clear stats or metrics and get creative with them."
        "Avoid any trailing or leading text in your ouput and just output the queries."
    )

    completion = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return completion.choices[0].message.content
def initialize_game_state(hometeam, awayteam):
    return {
        "team_stats": {
            hometeam: defaultdict(lambda: {
                "points": 0,
                "assists": 0,
                "turnovers": 0,
                "team_rebounds": 0,
                "offensive_rebounds": 0,
                "defensive_rebounds": 0,
                "timeouts_taken": 0,
                "turnovers": 0,
                "attempted_field_goals": 0,
                "made_field_goals": 0,
                "attempted_three_pointers": 0,
                "made_three_pointers": 0,
                "attempted_free_throws": 0,
                "made_free_throws": 0,
                "field_goal_percentage": 0,
                "three_point_percentage": 0,
                "free_throw_percentage": 0,
            }),
            awayteam: defaultdict(lambda: {
                "points": 0,
                "assists": 0,
                "turnovers": 0,
                "team_rebounds": 0,
                "offensive_rebounds": 0,
                "defensive_rebounds": 0,
                "timeouts_taken": 0,
                "turnovers": 0,
                "attempted_field_goals": 0,
                "made_field_goals": 0,
                "attempted_three_pointers": 0,
                "made_three_pointers": 0,
                "attempted_free_throws": 0,
                "made_free_throws": 0,
                "field_goal_percentage": 0,
                "three_point_percentage": 0,
                "free_throw_percentage": 0,
            }),
        },
        "player_stats": defaultdict(lambda: defaultdict(lambda: {
            "points": 0,
            "rebounds": 0,
            "assists": 0,
            "turnovers": 0,
            "two_pointers_attempted": 0,
            "two_pointers_made": 0,
            "three_pointers_attempted": 0,
            "three_pointers_made": 0,
            "free_throws_attempted": 0,
            "free_throws_made": 0,
            "field_goal_percentage": 0,
            "three_point_percentage": 0,
            "shots_blocked": 0,
            "own_shots_have_been_blocked": 0,
            "defensive_rebounds": 0,
            "offensive_rebounds": 0,
            "charges_taken": 0,
            "personal_fouls": 0,
            "goaltending_calls" : 0,
            "shooting_fouls": 0,
            "loose_ball_foul": 0,
            "violations": 0,
            "steals": 0,
            "bad_passes": 0,
            "turnovers": 0,
    }))
}
def initialize_summed_state():
    return defaultdict(lambda: {
            "points": 0,
            "rebounds": 0,
            "assists": 0,
            "turnovers": 0,
            "two_pointers_attempted": 0,
            "two_pointers_made": 0,
            "three_pointers_attempted": 0,
            "three_pointers_made": 0,
            "free_throws_attempted": 0,
            "free_throws_made": 0,
            "field_goal_percentage": 0,
            "three_point_percentage": 0,
            "shots_blocked": 0,
            "own_shots_have_been_blocked": 0,
            "defensive_rebounds": 0,
            "offensive_rebounds": 0,
            "charges_taken": 0,
            "personal_fouls": 0,
            "goaltending_calls" : 0,
            "shooting_fouls": 0,
            "loose_ball_foul": 0,
            "violations": 0,
            "steals": 0,
            "bad_passes": 0,
            "turnovers": 0,
        })

def parse_play_text(play_text):
    return_obj = {}
    if "blocks" in play_text:
        shot_type = "blocked_shot"
        blocker, shooter = play_text.split(" blocks ")
        shooter = shooter.split("'s")[0].strip()
        return_obj = {"shot_type": shot_type, "blocker": blocker, "shooter": shooter}
    elif 'defensive rebound' in play_text:
        rebounder = play_text.split(" defensive")[0]
        return_obj = {"shot_type": "rebound_defensive", "rebounder": rebounder}
    elif 'offensive rebound' in play_text:
        rebounder = play_text.split(" offensive")[0]
        return_obj = {"shot_type": "rebound_offensive", "rebounder": rebounder}
    elif 'team rebound' in play_text:
        team = play_text.split(" team")[0]
        return_obj = {"shot_type": "rebound_team", "rebounder": team}
    elif 'misses' in play_text:
        if 'free throw' in play_text:
            shot_type = "missed_free_throw"
        elif "three point" in play_text:
            shot_type = "missed_three_pointer"
        else:
            shot_type = "missed_two_pointer"
        shooter = play_text.split(" misses")[0]
        return_obj = {"shot_type": shot_type, "shooter": shooter}
    elif "kicked ball violation" in play_text:
        violator = play_text.split(" kicked")[0]
        return_obj = {"shot_type": "kicked_ball_violation", "violator": violator}
    
    # elif 'personal foul' in play_text:
    #     shot_type = 'personal_foul'
    #     fouler = play_text.split(" personal")[0]
    #     return {"shot_type": shot_type, "fouler": fouler}
    elif "charge" in play_text:
        charger = play_text.split(" charge")[0]
        return_obj = {"shot_type": "charge", "charger": charger}
    elif "loose ball foul" in play_text:
        fouler = play_text.split(" loose")[0]
        return_obj = {"shot_type": "loose_ball_foul", "fouler": fouler}
    elif "foul" in play_text:
        foul_type = play_text.split("foul")[0].strip().split()[-1]  
        fouler = play_text.split(foul_type + " foul")[0].strip()
        return_obj = {"shot_type": foul_type + "_foul", "fouler": fouler}
    elif "steals" in play_text and "bad pass" in play_text:
        stealer = play_text.split(" steals")[0].split("(")[-1].strip() 
        passer = play_text.split(" bad pass")[0].strip() 
        return_obj = {"shot_type": "steal", "stealer": stealer, "passer": passer}
    elif "turnover" in play_text and "steals" in play_text:
        stealer = play_text.split(" steals")[0].split("(")[-1].strip()
        turnover_player = play_text.split("lost ball turnover")[0].strip()
        return_obj = {"shot_type": "turnover_steal", "turnover_player": turnover_player, "stealer": stealer}
    elif "turnover" in play_text:
        turnover_player = (play_text.split()[0] + " " + play_text.split()[1]).strip()
        return_obj = {"shot_type": "turnover", "turnover_player": turnover_player}
    # elif "out of bounds lost ball" in play_text:
    #     out_of_bounds_player = play_text.split(" out")[0].strip()
    #     return_obj = {"shot_type": "out_of_bounds_lost_ball", "out_of_bounds_player": out_of_bounds_player}
    elif "out of bounds bad pass" in play_text:
        out_of_bounds_player = play_text.split(" out")[0].strip()
        return_obj = {"shot_type": "out_of_bounds_bad_pass", "out_of_bounds_player": out_of_bounds_player}

    elif "makes" in play_text:
        if "free throw" in play_text:
            points = 1
            shot_type = "free_throw"
        elif "three point" in play_text:
            points = 3
            shot_type = "three_pointer"
        else:
            points = 2
            shot_type = "two_pointer"
        shooter = play_text.split(" makes")[0]
        return_obj = {"shot_type": shot_type, "points": points, "scorer": shooter}
    elif "enters the game" in play_text:
        new_player = play_text.split(" enters")[0].strip()
        old_player = play_text.split(" for")[0].split("(")[-1].strip()
        return_obj = {"shot_type": "substitution", "new_player": new_player, "old_player": old_player}
    elif 'timeout' in play_text:
        team = play_text.split(" timeout")[0]
        return_obj = {"shot_type": "timeout", "team": team}
    elif 'vs.' in play_text:
        player1 = play_text.split(" vs. ")[0]
        player2 = play_text.split(" vs. ")[1].split(" ")[0]
        return_obj = {"shot_type": "jump_ball", "player1": player1, "player2": player2}
    elif 'CHALLENGE' in play_text:
        team = play_text.split("]")[0].split("[")[-1]
        return_obj = {"shot_type": "challenge", "team": team}
    elif "End of " in play_text:
        return_obj = {"shot_type": "end_of_quarter"}
    elif "traveling" in play_text:
        traveler = play_text.split(" traveling")[0]
        return_obj = {"shot_type": "traveling", "traveler": traveler}
    elif "REVIEW" in play_text:
        review_team = play_text.split("]")[0].split("[")[-1]
        return_obj = {"shot_type": "review", "review_team": review_team}
    elif "goaltending" in play_text:
        goaltender = (play_text.split()[0] + " " + play_text.split()[1]).strip()
        return_obj = {"shot_type": "goaltending", "goaltender": goaltender}
    elif "violation" in play_text:
        violator = (play_text.split()[0] + " " + play_text.split()[1]).strip()
        return_obj = {"shot_type": "violation", "violator": violator}
    
    if "assists" in play_text:
        assisted_by = play_text.split("assists")[0].split("(")[-1].strip()
        return_obj["assister"] = assisted_by

    return return_obj  

def build_game_stats(play_data, game_stats, summed_stats, hometeam, awayteam):
    def update_stats(play, stats, summed_stats, hometeam, awayteam):
        homeAway = play.get("homeAway")
        quarter = play["period"]["number"]

        if "shot clock" in play["text"]:
            return
        
        parsed_play = parse_play_text(play["text"])
        if parsed_play == {}:
            print("COULDNT PARSE THIS")
            print(play["text"])


        if parsed_play['shot_type'] == "free_throw" or parsed_play['shot_type'] == "two_pointer" or parsed_play['shot_type'] == "three_pointer":
            points, scorer, shot_type = parsed_play.get("points"), parsed_play.get("scorer"), parsed_play.get("shot_type")
            
            #update team points
            if homeAway == "home":
                stats["team_stats"][hometeam][quarter]["points"] += points
            else:
                stats["team_stats"][awayteam][quarter]["points"] += points
            if scorer:
                stats["player_stats"][scorer][quarter]["points"] += points
                summed_stats[scorer]["points"] += points
                if shot_type == "two_pointer":
                    stats["player_stats"][scorer][quarter]["two_pointers_attempted"] += 1
                    stats["player_stats"][scorer][quarter]["two_pointers_made"] += 1 if points == 2 else 0
                    stats["player_stats"][scorer][quarter]["field_goal_percentage"] = float((stats["player_stats"][scorer][quarter]["two_pointers_made"] + stats["player_stats"][scorer][quarter]["three_pointers_made"]) / (stats["player_stats"][scorer][quarter]["two_pointers_attempted"] + stats["player_stats"][scorer][quarter]["three_pointers_attempted"]))
                    summed_stats[scorer]["two_pointers_attempted"] += 1
                    summed_stats[scorer]["two_pointers_made"] += 1 if points == 2 else 0
                    summed_stats[scorer]["field_goal_percentage"] = float((summed_stats[scorer]["two_pointers_made"] + summed_stats[scorer]["three_pointers_made"]) / (summed_stats[scorer]["two_pointers_attempted"] + summed_stats[scorer]["three_pointers_attempted"]))

                    theteam = hometeam if homeAway == "home" else awayteam
                    stats['team_stats'][theteam][quarter]['attempted_field_goals'] += 1
                    stats['team_stats'][theteam][quarter]['made_field_goals'] += 1 if points == 2 else 0
                    stats['team_stats'][theteam][quarter]['field_goal_percentage'] = float(stats['team_stats'][theteam][quarter]['made_field_goals'] / stats['team_stats'][theteam][quarter]['attempted_field_goals'])
                elif shot_type == "three_pointer":
                    
                    stats["player_stats"][scorer][quarter]["three_pointers_attempted"] += 1
                    stats["player_stats"][scorer][quarter]["three_pointers_made"] += 1 if points == 3 else 0
                    stats["player_stats"][scorer][quarter]["three_point_percentage"] = float(stats["player_stats"][scorer][quarter]["three_pointers_made"] / stats["player_stats"][scorer][quarter]["three_pointers_attempted"])
                    stats["player_stats"][scorer][quarter]["field_goal_percentage"] = float((stats["player_stats"][scorer][quarter]["two_pointers_made"] + stats["player_stats"][scorer][quarter]["three_pointers_made"]) / (stats["player_stats"][scorer][quarter]["two_pointers_attempted"] + stats["player_stats"][scorer][quarter]["three_pointers_attempted"]))
                    summed_stats[scorer]["three_pointers_attempted"] += 1
                    summed_stats[scorer]["three_pointers_made"] += 1 if points == 3 else 0
                    summed_stats[scorer]["three_point_percentage"] = float(summed_stats[scorer]["three_pointers_made"] / summed_stats[scorer]["three_pointers_attempted"])
                    summed_stats[scorer]["field_goal_percentage"] = float((summed_stats[scorer]["two_pointers_made"] + summed_stats[scorer]["three_pointers_made"]) / (summed_stats[scorer]["two_pointers_attempted"] + summed_stats[scorer]["three_pointers_attempted"]))

                    theteam = hometeam if homeAway == "home" else awayteam
                    stats['team_stats'][theteam][quarter]['attempted_three_pointers'] += 1
                    stats['team_stats'][theteam][quarter]['made_three_pointers'] += 1 if points == 3 else 0
                    stats['team_stats'][theteam][quarter]['three_point_percentage'] = float(stats['team_stats'][theteam][quarter]['made_three_pointers'] / stats['team_stats'][theteam][quarter]['attempted_three_pointers'])
                elif shot_type == "free_throw":
                    stats["player_stats"][scorer][quarter]["free_throws_attempted"] += 1
                    stats["player_stats"][scorer][quarter]["free_throws_made"] += 1 if points == 1 else 0
                    summed_stats[scorer]["free_throws_attempted"] += 1
                    summed_stats[scorer]["free_throws_made"] += 1 if points == 1 else 0

                    theteam = hometeam if homeAway == "home" else awayteam
                    stats['team_stats'][theteam][quarter]['attempted_free_throws'] += 1
                    stats['team_stats'][theteam][quarter]['made_free_throws'] += 1 if points == 1 else 0
                    stats['team_stats'][theteam][quarter]['free_throw_percentage'] = float(stats['team_stats'][theteam][quarter]['made_free_throws'] / stats['team_stats'][theteam][quarter]['attempted_free_throws'])
        elif parsed_play['shot_type'] == "blocked_shot":
            blocker, shooter = parsed_play.get("blocker"), parsed_play.get("shooter")
            stats["player_stats"][blocker][quarter]["shots_blocked"] += 1
            stats["player_stats"][shooter][quarter]["own_shots_have_been_blocked"] += 1
            stats["player_stats"][shooter][quarter]["two_pointers_attempted"] += 1
            summed_stats[blocker]["shots_blocked"] += 1
            summed_stats[shooter]["own_shots_have_been_blocked"] += 1
            summed_stats[shooter]["two_pointers_attempted"] += 1

        elif parsed_play['shot_type'] == "rebound_defensive":
            rebounder = parsed_play.get("rebounder")
            stats["player_stats"][rebounder][quarter]["defensive_rebounds"] += 1
            summed_stats[rebounder]["defensive_rebounds"] += 1

            theteam = hometeam if homeAway == "home" else awayteam
            stats["team_stats"][theteam][quarter]["defensive_rebounds"] += 1
        elif parsed_play['shot_type'] == "rebound_offensive":
            rebounder = parsed_play.get("rebounder")
            stats["player_stats"][rebounder][quarter]["offensive_rebounds"] += 1
            summed_stats[rebounder]["offensive_rebounds"] += 1

            theteam = hometeam if homeAway == "home" else awayteam
            stats["team_stats"][theteam][quarter]["offensive_rebounds"] += 1
        elif parsed_play['shot_type'] == "rebound_team":
            rebounder = parsed_play.get("rebounder")
            if homeAway == "home":
                stats["team_stats"][hometeam][quarter]["team_rebounds"] += 1
            else:
                stats["team_stats"][awayteam][quarter]["team_rebounds"] += 1
        elif parsed_play['shot_type'] == "missed_free_throw":
            shooter = parsed_play.get("shooter")
            stats["player_stats"][shooter][quarter]["free_throws_attempted"] += 1
            stats["player_stats"][shooter][quarter]["free_throw_perctange"] = float(stats["player_stats"][shooter][quarter]["free_throws_made"] / stats["player_stats"][shooter][quarter]["free_throws_attempted"])
            summed_stats[shooter]["free_throws_attempted"] += 1
            summed_stats[shooter]["free_throw_perctange"] = float(summed_stats[shooter]["free_throws_made"] / summed_stats[shooter]["free_throws_attempted"])

            theteam = hometeam if homeAway == "home" else awayteam
            stats['team_stats'][theteam][quarter]['attempted_free_throws'] += 1
            stats['team_stats'][theteam][quarter]['free_throw_percentage'] = float(stats['team_stats'][theteam][quarter]['made_free_throws'] / stats['team_stats'][theteam][quarter]['attempted_free_throws'])
        elif parsed_play['shot_type'] == "missed_three_pointer":
            shooter = parsed_play.get("shooter")
            stats["player_stats"][shooter][quarter]["three_pointers_attempted"] += 1
            stats["player_stats"][shooter][quarter]["three_point_percentage"] = float(stats["player_stats"][shooter][quarter]["three_pointers_made"] / stats["player_stats"][shooter][quarter]["three_pointers_attempted"])
            stats["player_stats"][shooter][quarter]["field_goal_percentage"] = float((stats["player_stats"][shooter][quarter]["two_pointers_made"] + stats["player_stats"][shooter][quarter]["three_pointers_made"]) / (stats["player_stats"][shooter][quarter]["two_pointers_attempted"] + stats["player_stats"][shooter][quarter]["three_pointers_attempted"]))
            summed_stats[shooter]["three_pointers_attempted"] += 1
            summed_stats[shooter]["three_point_percentage"] = float(summed_stats[shooter]["three_pointers_made"] / summed_stats[shooter]["three_pointers_attempted"])
            summed_stats[shooter]["field_goal_percentage"] = float((summed_stats[shooter]["two_pointers_made"] + summed_stats[shooter]["three_pointers_made"]) / (summed_stats[shooter]["two_pointers_attempted"] + summed_stats[shooter]["three_pointers_attempted"]))

            theteam = hometeam if homeAway == "home" else awayteam
            stats['team_stats'][theteam][quarter]['attempted_three_pointers'] += 1
            stats['team_stats'][theteam][quarter]['three_point_percentage'] = float(stats['team_stats'][theteam][quarter]['made_three_pointers'] / stats['team_stats'][theteam][quarter]['attempted_three_pointers'])
        elif parsed_play['shot_type'] == "missed_two_pointer":
            shooter = parsed_play.get("shooter")
            stats["player_stats"][shooter][quarter]["two_pointers_attempted"] += 1
            stats["player_stats"][shooter][quarter]["field_goal_percentage"] = float((stats["player_stats"][shooter][quarter]["two_pointers_made"] + stats["player_stats"][shooter][quarter]["three_pointers_made"]) / (stats["player_stats"][shooter][quarter]["two_pointers_attempted"] + stats["player_stats"][shooter][quarter]["three_pointers_attempted"]))
            summed_stats[shooter]["two_pointers_attempted"] += 1
            summed_stats[shooter]["field_goal_percentage"] = float((summed_stats[shooter]["two_pointers_made"] + summed_stats[shooter]["three_pointers_made"]) / (summed_stats[shooter]["two_pointers_attempted"] + summed_stats[shooter]["three_pointers_attempted"]))

            theteam = hometeam if homeAway == "home" else awayteam
            stats['team_stats'][theteam][quarter]['attempted_field_goals'] += 1
            stats['team_stats'][theteam][quarter]['field_goal_percentage'] = float(stats['team_stats'][theteam][quarter]['made_field_goals'] / stats['team_stats'][theteam][quarter]['attempted_field_goals'])
        elif parsed_play['shot_type'] == "charge":
            charger = parsed_play.get("charger")
            stats["player_stats"][charger][quarter]["charges_taken"] += 1
            summed_stats[charger]["charges_taken"] += 1
        elif parsed_play['shot_type'] == "personal_foul":
            fouler = parsed_play.get("fouler")
            stats["player_stats"][fouler][quarter]["personal_fouls"] += 1
            summed_stats[fouler]["personal_fouls"] += 1
        elif parsed_play['shot_type'] == 'shooting_foul':
            fouler = parsed_play.get("fouler")
            stats["player_stats"][fouler][quarter]["shooting_fouls"] += 1
            summed_stats[fouler]["shooting_fouls"] += 1
        elif parsed_play['shot_type'] == 'loose_ball_foul':
            fouler = parsed_play.get("fouler")
            stats["player_stats"][fouler][quarter]["loose_ball_foul"] += 1
            summed_stats[fouler]["loose_ball_foul"] += 1
        elif parsed_play['shot_type'] == 'steal':
            stealer = parsed_play.get("stealer")
            passer = parsed_play.get("passer")
            stats["player_stats"][stealer][quarter]["steals"] += 1
            stats["player_stats"][passer][quarter]["bad_passes"] += 1
            summed_stats[stealer]["steals"] += 1
            summed_stats[passer]["bad_passes"] += 1
        elif parsed_play['shot_type'] == 'turnover_steal':
            turnover_player = parsed_play.get("turnover_player")
            stealer = parsed_play.get("stealer")
            stats["player_stats"][turnover_player][quarter]["turnovers"] += 1
            stats["player_stats"][stealer][quarter]["steals"] += 1
            summed_stats[turnover_player]["turnovers"] += 1
            summed_stats[stealer]["steals"] += 1
            if homeAway == "home":
                stats["team_stats"][hometeam][quarter]["turnovers"] += 1
            else:
                stats["team_stats"][awayteam][quarter]["turnovers"] += 1
        elif parsed_play['shot_type'] == 'turnover':
            turnover_player = parsed_play.get("turnover_player")
            stats["player_stats"][turnover_player][quarter]["turnovers"] += 1
            summed_stats[turnover_player]["turnovers"] += 1
            if homeAway == "home":
                stats["team_stats"][hometeam][quarter]["turnovers"] += 1
            else:
                stats["team_stats"][awayteam][quarter]["turnovers"] += 1
        elif parsed_play['shot_type'] == 'timeout':
            team = parsed_play.get("team")
            if homeAway == "home":
                stats["team_stats"][hometeam][quarter]["timeouts_taken"] += 1
            else:
                stats["team_stats"][awayteam][quarter]["timeouts_taken"] += 1
        elif parsed_play['shot_type'] == 'violation':
            violator = parsed_play.get("violator")
            stats["player_stats"][violator][quarter]["personal_fouls"] += 1
            summed_stats[violator]["personal_fouls"] += 1
        elif parsed_play['shot_type'] == 'goaltending':
            goaltender = parsed_play.get("goaltender")
            stats["player_stats"][goaltender][quarter]["goaltending_calls"] += 1
            summed_stats[goaltender]["goaltending_calls"] += 1

        if "assister" in parsed_play:
            assister = parsed_play.get("assister")
            stats["player_stats"][assister][quarter]["assists"] += 1
            summed_stats[assister]["assists"] += 1
            if homeAway == "home":
                stats["team_stats"][hometeam][quarter]["assists"] += 1
            else:
                stats["team_stats"][awayteam][quarter]["assists"] += 1


    for play in play_data:
        update_stats(play, game_stats, summed_stats, hometeam, awayteam)

    return game_stats, summed_stats


def extract_player_names(play_text, hometeam, awayteam):
    if hometeam in play_text:
        return [hometeam]
    elif awayteam in play_text:
        return [awayteam]

    if "End of " in play_text:
        return play_text
    
    if "turnover"  in play_text:
        return play_text
    
    # Use regex to match 'Firstname Lastname' patterns for player names
    name_pattern = r"([A-Z][a-z]+(?: [A-Z][a-z]+)+)"  # Handles multiple name parts like 'Lindy Waters III'
    matches = re.findall(name_pattern, play_text)
    if matches:
        return matches

    name_pattern = r"([A-Z][a-z]+(?: [A-Z][a-z]+|[A-Z]\.)+)"
    matches = re.findall(name_pattern, play_text)
    if matches:
        return matches
    
    name_pattern = r"([A-Z][a-z]*[A-Z][a-z]*(?: [A-Z][a-z]+)+)"
    matches = re.findall(name_pattern, play_text)
    if matches:
        return matches
    

def make_hashable(item):
    if isinstance(item, dict):
        return frozenset((key, make_hashable(value)) for key, value in item.items())
    elif isinstance(item, list):
        return tuple(make_hashable(x) for x in item)
    return item  

def find_new_dicts(list_b, play_map):
    returnlist = []
    for i in list_b:
        hashed = make_dict_hashable(i)
        if hashed not in play_map:
            play_map[hashed] = 1
            returnlist.append(i)
    return returnlist, play_map

#convert dict to string
def make_dict_hashable(d, cache={}):
    return json.dumps(d, sort_keys=True) 



def extract_player_name_from_query(query):
    name_pattern = r"([A-Z][a-z]+ [A-Z][a-z]+)"
    matches = re.findall(name_pattern, query)
    
    if matches:
        return matches[0]
    
    return None

def extract_team_name_from_query(query, known_teams):
    query_lower = query.lower()    
    for team in known_teams:
        if team.lower() in query_lower:
            return team  # Return the first matched team name
    
    return None

def query_game_stats(query):
    team_name = extract_team_name_from_query(query, [game_info['team1'], game_info['team2']])  
    if team_name:
        return GAME_STATS.get('team_stats', {}).get(team_name, {})
    
    player_name = extract_player_name_from_query(query)  
    if player_name:
        player_stats = GAME_STATS.get('player_stats', {}).get(player_name, {})
        return player_stats if player_stats else "Player not found"
    
    return "No relevant game stats found for this query."

def query_game_stats_summed(query):
    player_name = extract_player_name_from_query(query)  
    if player_name:
        player_stats = SUMMED_STATS.get(player_name, {})
        return player_stats if player_stats else "Player not found"
    
    return "No relevant game stats found for this query."


def search_statmuse(query: str) -> str:
  URL = f'https://www.statmuse.com/nba/ask/{query}'
  page = requests.get(URL)
  
  soup = BeautifulSoup(page.content, "html.parser")
  return soup.find("div", class_="flex flex-col justify-between @lg/hero:items-start").text

# search_out = search_statmuse("Who is the highest scoring player on the Los Angeles Lakers of all time")
# print(search_out)

statmuse_tool = Tool(
    name = "Statmuse",
    func = search_statmuse,
    description = "A sports search engine. Use this more than normal search if the question is about NBA basketball, like 'who is the highest scoring player in the NBA?'. Always specify a year or timeframe with your search. Only ask about one player or team at a time, don't ask about multiple players at once."
)

serpapi = SerpAPIWrapper(serpapi_api_key=serp_api_key)
serpapi_tool = Tool(
    name="SerpAPI",
    description="Use this tool to search the web for information.",
    func=serpapi.run
)

context_tool = Tool(
    name="Currentgame",
    description="Use this to get per quarter information/context about the current team and players in the current game",
    func=query_game_stats
)

summed_context_tool = Tool(
    name="CurrentgameSummed",
    description="Use this to get whole game information/context about the current team and players in the current game",
    func=query_game_stats_summed
)

tools = [statmuse_tool, serpapi_tool, context_tool, summed_context_tool]

llm = ChatOpenAI(model="gpt-4o", temperature=0, api_key=open_ai_key)
llm_with_tools = llm.bind_tools(tools)

# tools = load_tools(["serpapi", "llm-math"], llm=llm, serpapi_api_key="d08e104f693e95d6dfa1194e4e560db5239643147352af8ed4881a9e5be5d7cd") + [statmuse_tool]

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You must provide only the strict answer to the query without any additional text, context, or explanation."),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)

agent = (
    {
        "input": lambda x: x["input"],
        "agent_scratchpad": lambda x: format_to_openai_tool_messages(
            x["intermediate_steps"]
        ),
    }
    | prompt
    | llm_with_tools
    | OpenAIToolsAgentOutputParser()
)

agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=False)


def parse_table(table):
    # Get all the header cells (th elements)
    headers = table.find_all('th')
    header_text = [header.get_text(strip=True) for header in headers]
    
    # Print the headers
    # print("Headers: ", header_text)

    # Get all rows in the table (excluding the header row)
    rows = table.find_all('tr')
    table_map = {}

    # Iterate through the rows and print each row's data
    for row_idx, row in enumerate(rows):
        # Get all cells (td elements) in the row
        cells = row.find_all('td')
        
        if not cells:  # Skip the row if it's empty (like the header row)
            continue
        
        row_data = [cell.get_text(strip=True) for cell in cells]
        
        # Print the row index and its corresponding data
        # print(f"Row {row_idx + 1}: {row_data}")
        table_map[row_idx] = row_data
    
    return table_map

# WebSocket instance (to allow sending messages from the UI)
ws_instance = None


game_id = 401705015
game_url = f"https://www.espn.com/nba/playbyplay/_/gameId/{game_id}"
game_info = {
    'team1': 'Boston Celtics', #home
    'team2': 'Toronto Raptors', #away
    'date': 'Decmber 31, 2024',
}
current_window_of_plays = {}
global_compound_queries = set()
key_moments_agg = []
key_moment_length_since_last_query = 0
home_team_id = id_to_team[game_info['team1']]
away_team_id = id_to_team[game_info['team2']]
id_to_play = {}
id_to_play_data = {}
count_to_id = {}
id_to_play_info = {}
num_plays = 0
PLAY_IDX = 0
GAME_STATS = initialize_game_state(game_info['team1'], game_info['team2'])
SUMMED_STATS = initialize_summed_state()

def on_message(ws, message):
    """
    Callback for receiving WebSocket messages.
    Updates the global list and UI.
    """
    global incoming_messages
    global query_output
    global GAME_STATS
    global SUMMED_STATS
    data = json.loads(message)

    if data.get("op") == "C" and data.get("rc") == 200:
        #send the S messages
        sid = data.get("sid")
        print("retrieved session id " + sid)
        msg = {
            "op": "S",
            "sid": sid,
            "tc": f"gp-basketball-nba-{game_id}"
        }
        ws.send(json.dumps(msg))

        msg = {
            "op": "S",
            "sid": sid,
            "tc": "event-basketball-nba"
        }
        ws.send(json.dumps(msg))

    # Add message to global list

    if data.get('pl') != None:
        try:
            pl = json.loads(data.get('pl'))
            if type(pl) == dict:
                pl = pl.get('pl')
                if type(pl) != str:
                    return
                compressed_raw = base64.b64decode(pl)
                decompressed_data = zlib.decompress(compressed_raw)
                result = json.loads(decompressed_data)
                pattern = r'^/plays/\d+/text$'
                if type(result) == list:
                    for r in result:
                        play_occur = False
                        if 'op' in r and r['op'] == 'add' and 'path' in r and r['path'] == '/plays/-':
                            play_text = r['value']['text']
                            play_id = r['value']['id']
                            play_clock = r['value']['clock']
                            play_period = r['value']['period']
                            play_home_score = r['value']['homeScore']
                            play_away_score = r['value']['awayScore']

                            # if 'team' not in r['value']:
                            #     print("no team")
                            #     print(play_text)
                            # team_id = r['value']['team']['id']
                            # if team_id == home_team_id:
                            #     play_home_away = 'home'
                            # else:
                            #     play_home_away = 'away'

                            global PLAY_IDX
                            

                            id_to_play[play_id] = play_text
                            id_to_play_data[play_id] = r['value']
                            count_to_id[PLAY_IDX] = play_id
                            PLAY_IDX += 1

                            print("----NEW PLAY----")
                            incoming_messages.append("----NEW PLAY----")
                            print("[" + play_clock['displayValue'] + "] " + play_text)
                            incoming_messages.append("[" + play_clock['displayValue'] +" Q" + str(play_period['number']) + "] " + play_text)

                            play_occur = True

                            if play_text == "End of Game":
                                return

                        elif 'op' in r and r['op'] == 'replace' and 'path' in r and re.match(pattern, r['path']):
                            #split on /
                            splits = r['path'].split('/')
                            play_count = splits[2]
                            play_text = r['value']

                            
                            if int(play_count) in count_to_id:
                                play_id = count_to_id[int(play_count)]
                                id_to_play[play_id] = play_text
                                id_to_play_data[play_id]['text'] = play_text

                                print("----MODIFIED PLAY----")
                                incoming_messages.append("----MODIFIED PLAY----")
                                print(play_text)
                                incoming_messages.append(play_text)

                                play_occur = True
                            else:
                                # totallen = len(count_to_id)
                                # print(id_to_play[count_to_id[totallen - 1]])
                                print("the val")
                                print(play_count)
                                print(count_to_id)
                                print(play_text)
                                
                                print("og play doesnt exist to replace")
                                return
                            
                        if play_occur:
                            global current_window_of_plays
                            if play_id not in current_window_of_plays:
                                newdict = {"text": id_to_play_data[play_id]['text'], "id": id_to_play_data[play_id]['id'], "clock": id_to_play_data[play_id]['clock'], "period": id_to_play_data[play_id]['period'], "homeAway": id_to_play_data[play_id]['homeAway'] if "homeAway" in id_to_play_data[play_id] else ("home" if id_to_play_data[play_id]['team']['id'] == home_team_id else "away"), 
                                           "homeScore": id_to_play_data[play_id]['homeScore'], "awayScore": id_to_play_data[play_id]['awayScore']}
                                current_window_of_plays[play_id] = newdict
                            else:
                                current_window_of_plays[play_id]["text"] = play_text
                            added_play = current_window_of_plays[play_id]
                            GAME_STATS, SUMMED_STATS = build_game_stats([added_play], GAME_STATS, SUMMED_STATS, game_info['team1'], game_info['team2'])
                            parsed_play = parse_play_text(added_play['text'])
                            del parsed_play['shot_type']
                            if 'team' in parsed_play: del parsed_play['team']
                            if 'points' in parsed_play: del parsed_play['points']
                            
                            for item in box_score_tree.get_children():
                                for player in parsed_play.values():
                                    if player in box_score_tree.item(item, "tags"):
                                        statlist = [player, SUMMED_STATS[player]["points"],
                                            SUMMED_STATS[player]["rebounds"],
                                            SUMMED_STATS[player]["assists"],
                                            SUMMED_STATS[player]["turnovers"],
                                            str(SUMMED_STATS[player]["two_pointers_made"]) + "-" + str(SUMMED_STATS[player]["two_pointers_attempted"]),
                                            str(SUMMED_STATS[player]["three_pointers_made"] )+ "-" + str(SUMMED_STATS[player]["three_pointers_attempted"]),
                                            str(SUMMED_STATS[player]["free_throws_made"]) + "-" + str(SUMMED_STATS[player]["free_throws_attempted"]),
                                            str(SUMMED_STATS[player]["field_goal_percentage"] * 100),
                                            str(SUMMED_STATS[player]["three_point_percentage"] * 100),
                                            SUMMED_STATS[player]["defensive_rebounds"],
                                            SUMMED_STATS[player]["offensive_rebounds"],
                                            SUMMED_STATS[player]["charges_taken"],
                                            SUMMED_STATS[player]["personal_fouls"],
                                            SUMMED_STATS[player]["shots_blocked"],
                                            SUMMED_STATS[player]["steals"]
                                            ]
                                        box_score_tree.item(item, values=tuple(statlist))
                                        break
                            

                        if len(current_window_of_plays) == 5:
                            global key_moments_agg
                            global global_compound_queries
                            global key_moment_length_since_last_query
                            
                            key_moments_current = process_play_by_play(list(current_window_of_plays.values())) 
                            key_moments_agg.extend(key_moments_current)
                            
                            if len(key_moments_agg) > key_moment_length_since_last_query:
                                print("querying\n")
                                key_moment_length_since_last_query = len(key_moments_agg)

                                compound_queries = generate_queries_with_gpt(key_moments_agg, game_info)

                                compound_queries = compound_queries.strip().split('\n')
                                compound_queries = [q.strip() for q in compound_queries if q.strip()]
                                compound_queries = [re.sub(r'^\d+\.\s*', '', q.strip()) for q in compound_queries if q.strip()]

                                for cq in compound_queries:
                                    if cq not in global_compound_queries:
                                        # print("---QUERY: " + cq)
                                        thelist = list(agent_executor.stream({"input": cq}))
                                        # print("----ANSWER---- " + thelist[-1]['output'])
                                        print(thelist[-1]['output'])
                                        print("------------------------------------------------------------------")

                                        query_output.append(thelist[-1]['output'])
                                        running_list.delete(1.0, tk.END)
                                        running_list.insert(tk.END, "\n\n".join(query_output))  # Show last 20 messages
                                        running_list.see(tk.END)
                                global_compound_queries.update(compound_queries)
                        
                            current_window_of_plays = {}

        except json.JSONDecodeError:
            pass

    # Update the WebSocket and Box Score panels after receiving a message
    update_ui()

def on_error(ws, error):
    print(f"WebSocket Error: {error}")
    traceback.print_exc()

def on_close(ws, close_status_code, close_msg):
    print(f"WebSocket Closed: {close_msg}")

def on_open(ws):
    print("Socket open.")
    # Send the initial message after opening the socket
    initial_message = '{"op": "C"}'
    ws.send(initial_message)

    with urllib.request.urlopen(game_url) as response:
        html = response.read()
    
    soup = BeautifulSoup(html, 'html.parser')
    script_tag = soup.find('script', string=lambda x: x and 'playGrps' in x)
    script_content = script_tag.string

    pattern = r'(\{"playGrps.*?}}]])'
    match = re.search(pattern, script_content, re.DOTALL)

    if match:
        extracted_text = match.group(1)
        extracted_text += "}"
        raw_play_data = json.loads(extracted_text)['playGrps']

        raw_all_plays = []

        for quarter in raw_play_data:
            raw_all_plays.extend(quarter)

        raw_all_plays.reverse()

        for i, play in enumerate(raw_all_plays):
            play_text = play['text']
            play_id = play['id']

            id_to_play[play_id] = play_text
            id_to_play_data[play_id] = play
            count_to_id[i] = play_id

            incoming_messages.append(str(i) + "     " + "[" + play['clock']['displayValue'] +" Q" + str(play['period']['number']) + "] " + play_text)


        global PLAY_IDX
        PLAY_IDX = len(raw_all_plays) - 1
        PLAY_IDX += 1

        global GAME_STATS
        global SUMMED_STATS
        GAME_STATS, SUMMED_STATS = build_game_stats(raw_all_plays, GAME_STATS,SUMMED_STATS, game_info['team1'], game_info['team2'])

        # SUMMED_STATS = {
        #     key: {sub_key: sum(d[sub_key] for d in nested_dicts.values()) for sub_key in nested_dicts['dict1']}
        #     for key, nested_dicts in GAME_STATS['player_stats'].items()
        # }

        for player in SUMMED_STATS:
            statlist = [player, SUMMED_STATS[player]["points"],
                        SUMMED_STATS[player]["rebounds"],
                        SUMMED_STATS[player]["assists"],
                        SUMMED_STATS[player]["turnovers"],
                        str(SUMMED_STATS[player]["two_pointers_made"]) + "-" + str(SUMMED_STATS[player]["two_pointers_attempted"]),
                        str(SUMMED_STATS[player]["three_pointers_made"] )+ "-" + str(SUMMED_STATS[player]["three_pointers_attempted"]),
                        str(SUMMED_STATS[player]["free_throws_made"]) + "-" + str(SUMMED_STATS[player]["free_throws_attempted"]),
                        SUMMED_STATS[player]["field_goal_percentage"],
                        SUMMED_STATS[player]["three_point_percentage"],
                        SUMMED_STATS[player]["defensive_rebounds"],
                        SUMMED_STATS[player]["offensive_rebounds"],
                        SUMMED_STATS[player]["charges_taken"],
                        SUMMED_STATS[player]["personal_fouls"],
                        SUMMED_STATS[player]["shots_blocked"],
                        SUMMED_STATS[player]["steals"]
                        ]
            box_score_tree.insert("", tk.END, tags=(statlist[0],), iid=statlist[0], values=tuple(statlist))

def on_button_click():
    user_input = chat_input.get()
    chat_input.delete(0, tk.END)  # Clear the input field
    chat_messages.append("You: " + user_input)

    thelist = list(agent_executor.stream({"input": user_input}))
    chat_output = thelist[-1]['output']
    chat_messages.append("Output: " + chat_output + "\n")
    
    chat_text.delete(1.0, tk.END)
    chat_text.insert(tk.END, "\n".join(chat_messages))  # Show last 20 messages
    chat_text.see(tk.END)
    

def start_websocket(url):
    """
    Starts the WebSocket client and listens for messages.
    """
    global ws_instance
    ws_instance = WebSocketApp(
        url,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
        on_open=on_open
    )
    ws_instance.run_forever()

def start_websocket_thread():
    """
    Launch the WebSocket listener in a separate thread.
    """
    # ws_uri = "wss://echo.websocket.org"
    ws_uri = "wss://pw58c9f642-1f2f-47a3-b1af-4f5bd61b99a4-35-91-9-49.fastcast.semfs.engsvc.go.com:9573/FastcastService/pubsub/profiles/12000?TrafficManager-Token=MTczNTY4MzkwMjMzMw==:vGFzkwO4GFoHSBbrNufKnD41OeQ="
    ws_thread = threading.Thread(target=start_websocket, args=(ws_uri,))
    ws_thread.daemon = True
    ws_thread.start()

def update_box_score():
    """
    Updates the Box Score panel with game stats data.
    """
    global GAME_STATS
    # Clear the Treeview
    for row in box_score_tree.get_children():
        box_score_tree.delete(row)

    # Add game stats to the Treeview
    for player in GAME_STATS['player_stats']:
        statlist = [player, GAME_STATS['player_stats'][player]["points"],
                    GAME_STATS['player_stats'][player]["rebounds"],
                    GAME_STATS['player_stats'][player]["assists"],
                    GAME_STATS['player_stats'][player]["turnovers"],
                    str(GAME_STATS['player_stats'][player]["two_pointers_made"]) + "-" + str(GAME_STATS['player_stats'][player]["two_pointers_attempted"]),
                    str(GAME_STATS['player_stats'][player]["three_pointers_made"] )+ "-" + str(GAME_STATS['player_stats'][player]["three_pointers_attempted"]),
                    str(GAME_STATS['player_stats'][player]["free_throws_made"]) + "-" + str(GAME_STATS['player_stats'][player]["free_throws_attempted"]),
                    GAME_STATS['player_stats'][player]["field_goal_percentage"],
                    GAME_STATS['player_stats'][player]["three_point_percentage"],
                    GAME_STATS['player_stats'][player]["defensive_rebounds"],
                    GAME_STATS['player_stats'][player]["offensive_rebounds"],
                    GAME_STATS['player_stats'][player]["charges_taken"],
                    GAME_STATS['player_stats'][player]["personal_fouls"],
                    GAME_STATS['player_stats'][player]["shots_blocked"],
                    GAME_STATS['player_stats'][player]["steals"]
                    ]
    
        box_score_tree.insert(
            "", tk.END,
            values=tuple(statlist)
        )

def update_ui():
    """
    Update the UI panels to reflect the current list of incoming messages.
    """
    # Update WebSocket Panel
    websocket_text.delete(1.0, tk.END)
    websocket_text.insert(tk.END, "\n".join(incoming_messages))  # Show last 20 messages
    websocket_text.see(tk.END)

    # Update Box Score Panel
    # update_box_score()
    
    

    # Schedule the next UI update
    # root.after(100, update_ui)  # Refresh every 100 ms

# Main UI
root = tk.Tk()
root.title("Courtside")
root.geometry("1000x750")

icon = PhotoImage(file="nba.png")  # Replace with the path to your .png file
root.iconphoto(True, icon)

nba_blue = "#006BB6"  # NBA Blue
nba_red = "#9C2D32"   # NBA Red
nba_white = "#FFFFFF"  # NBA White
dark_bg = "#2E2E2E"    # Dark background for the UI
light_bg = "#444444"   # Lighter background for some elements
button_bg = "#555555"  # Button background
button_fg = "#FFFFFF"  # Button text color
text_fg = "#FFFFFF"    # Text foreground color (for dark backgrounds)
header_fg = "#FFFFFF"  # Header label text color
highlight_color = "#B2B2B2"  # Light gray for highlighting selected rows
treeview_bg = "#333333"  # Treeview background color
treeview_fg = "#FFFFFF"  # Treeview text color
treeview_sel_bg = "#444444"  # Treeview selected background color


title_frame = tk.Frame(root, bg=nba_blue)
title_frame.grid(row=0, column=0, columnspan=2, pady=0, sticky="ew")

# Title Text
title_label = tk.Label(title_frame, text=game_info["team2"] + " at " + game_info['team1'], font=("Arial", 20, "bold"), fg=header_fg, bg=nba_blue)
title_label.grid(row=0, column=0, sticky="w", padx=10)

# Subtitle Text
subtitle_label = tk.Label(title_frame, text=game_info['date'], font=("Arial", 14),fg=header_fg, bg=nba_blue)
subtitle_label.grid(row=1, column=0, sticky="w", padx=10)

# Top Left: WebSocket Panel
websocket_frame = tk.Frame(root, bg=dark_bg, padx=10, pady=5)
websocket_frame.grid(row=1, column=0, sticky="nsew")
websocket_label = tk.Label(websocket_frame, text="Play by Play", font=("Arial", 14), fg=header_fg, bg=dark_bg)
websocket_label.pack()

websocket_text_frame = tk.Frame(websocket_frame, bg=light_bg)

v_scrollbar = tk.Scrollbar(websocket_text_frame, orient="vertical")


websocket_text = tk.Text(websocket_text_frame, wrap=tk.WORD, height=10, width=40, fg=text_fg, bg=light_bg, yscrollcommand=v_scrollbar.set)
websocket_text.pack(side="left", expand=True, fill="both")

v_scrollbar.pack(side="right", fill="y")
v_scrollbar.config(command=websocket_text.yview)

websocket_text_frame.pack(expand=True, fill="both")


# websocket_input = tk.Entry(websocket_frame, width=30)
# websocket_input.pack(pady=5)
# websocket_send_btn = tk.Button(websocket_frame, text="Send", command=lambda: None)
# websocket_send_btn.pack()

# v_scrollbar = tk.Scrollbar(websocket_frame, orient="vertical")
# v_scrollbar.pack(side="right", fill="y")
# v_scrollbar.config(command=websocket_text.yview)

# Top Right: Box Score and Running List Panel
box_score_frame = tk.Frame(root, bg=dark_bg, padx=5, pady=5)
box_score_frame.grid(row=1, column=1, sticky="nsew")

# Box Score Sub-Panel
box_score_label = tk.Label(box_score_frame, text="Box Score", font=("Arial", 14), fg=header_fg, bg=dark_bg)
box_score_label.pack()
box_score_tree = ttk.Treeview(box_score_frame, columns=("Player", "PTS", "REB", "AST", "TO", "2PT", "3PT", "FT", "FG %", "3PT %", "DREB", "OREB", "CHRG", "PF", "BLK", "STL"), show="headings", height=20)
box_score_tree.pack()

style = ttk.Style()
style.configure("Treeview", background=treeview_bg, foreground=treeview_fg, fieldbackground=treeview_bg)
style.configure("Treeview.Heading", background="#00FF00", foreground=dark_bg)
style.map("Treeview", background=[('selected', treeview_sel_bg)])

h_scrollbar = tk.Scrollbar(box_score_frame, orient="horizontal", command=box_score_tree.xview, bg=dark_bg)
h_scrollbar.pack(side="bottom", fill="x")
box_score_tree.config(xscrollcommand=h_scrollbar.set)

# Set column headings
box_score_tree.heading("Player", text="Player")
box_score_tree.heading("PTS", text="PTS")
box_score_tree.heading("REB", text="REB")
box_score_tree.heading("AST", text="AST")
box_score_tree.heading("TO", text="TO")
box_score_tree.heading("2PT", text="2PT")
box_score_tree.heading("3PT", text="3PT", anchor="w")
box_score_tree.heading("FT", text="FT")
box_score_tree.heading("FG %", text="FG %")
box_score_tree.heading("3PT %", text="3PT %")
box_score_tree.heading("DREB", text="DREB")
box_score_tree.heading("OREB", text="OREB")
box_score_tree.heading("CHRG", text="CHRG")
box_score_tree.heading("PF", text="PF")
box_score_tree.heading("BLK", text="BLK")
box_score_tree.heading("STL", text="STL")

# Set column widths
box_score_tree.column("Player", width=120)
box_score_tree.column("PTS", width=50)
box_score_tree.column("REB", width=50)
box_score_tree.column("AST", width=50)
box_score_tree.column("TO", width=50)
box_score_tree.column("2PT", width=50)
box_score_tree.column("3PT", width=50)
box_score_tree.column("FT", width=50)
box_score_tree.column("FG %", width=50)
box_score_tree.column("3PT %", width=50)
box_score_tree.column("DREB", width=50)
box_score_tree.column("OREB", width=50)
box_score_tree.column("CHRG", width=50)
box_score_tree.column("PF", width=50)
box_score_tree.column("BLK", width=50)
box_score_tree.column("STL", width=50)

# Running List Sub-Panel
# running_list_label = tk.Label(box_score_frame, text="Running List (WebSocket Messages)", font=("Arial", 14))
# running_list_label.pack()
# running_list_text = tk.Text(box_score_frame, wrap=tk.WORD, height=8, width=40)
# running_list_text.pack()

# Bottom Left: Chat Interface
chat_frame = tk.Frame(root, bg=dark_bg, padx=5, pady=5)
chat_frame.grid(row=2, column=0, sticky="nsew")
chat_label = tk.Label(chat_frame, text="Chat Interface", font=("Arial", 14), fg=header_fg, bg=dark_bg)
chat_label.pack()
chat_text = tk.Text(chat_frame, wrap=tk.WORD, height=10, width=40, fg=text_fg, bg=light_bg)
chat_text.pack(expand=True, fill="both")
chat_input = tk.Entry(chat_frame, width=30, fg=text_fg, bg=light_bg)
chat_input.pack(pady=5)
chat_send_btn = tk.Button(chat_frame, text="Send", command=on_button_click, fg=nba_blue, bg=nba_blue, activebackground="#0056b3"  )  # Replace with chat logic
chat_send_btn.pack()

# Bottom Right: Placeholder for Future Feature
running_list_frame = tk.Frame(root, bg=dark_bg, padx=5, pady=5)
running_list_frame.grid(row=2, column=1, sticky="nsew")

# Running List Label
running_list_label = tk.Label(running_list_frame, text="NBA Insights", font=("Arial", 14), fg=header_fg, bg=dark_bg)
running_list_label.pack()

# Running List Text Widget
running_list = tk.Text(running_list_frame, wrap=tk.WORD, height=10, width=40, fg=text_fg, bg=nba_red)
running_list.pack(expand=True, fill="both", side="left")

# Vertical Scrollbar
v_scrollbar = tk.Scrollbar(running_list_frame, orient="vertical", command=running_list.yview)
v_scrollbar.pack(side="right", fill="y")

# Link the scrollbar to the text widget
running_list.config(yscrollcommand=v_scrollbar.set)


# Configure grid weights
root.grid_rowconfigure(0, weight=0)
root.grid_rowconfigure(1, weight=1)
root.grid_rowconfigure(2, weight=1)
root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)

root.grid_columnconfigure(0, minsize=500)

# Start threads
start_websocket_thread()

# Start the UI update loop
update_ui()

# Main loop
root.mainloop()
