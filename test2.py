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
import threading
import tkinter as tk
from websocket import WebSocketApp
import requests
import json
from dotenv import load_dotenv
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
from langchain_community.agent_toolkits.load_tools import load_tools
from langchain.agents import Tool, AgentExecutor
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents.format_scratchpad.openai_tools import (
    format_to_openai_tool_messages,
)
from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser
from langchain.agents import AgentExecutor
from langchain_community.utilities import SerpAPIWrapper
from game_utils import (
    initialize_game_state,
    initialize_summed_state,
    process_play_by_play,
    parse_play_text,
    extract_team_name_from_query,
    extract_player_name_from_query
)
from utils import (
    generate_queries_with_gpt
)
# from agent import agent_executor
from build_current_game import (
    build_game_stats
)

#load from json file
with open('game_stats.json', 'r') as f:
    GAME_STATS  = json.load(f)

with open('summed_stats.json', 'r') as f:
    SUMMED_STATS  = json.load(f)

open_ai_key = os.getenv("OPENAI_APIKEY")
serp_api_key = os.getenv("SERP_APIKEY")

openai_client = OpenAI(
  api_key=open_ai_key,
)

game_info = {
    'team1': 'Cleveland Cavaliers', #home
    'team2': 'Miami Heat', #away
}


def query_game_stats(query):
    print("calling the query game stats funciton")
    print(query)
    team_name = extract_team_name_from_query(query, [game_info['team1'], game_info['team2']])  
    print("the gotten team name")
    print(team_name)
    if team_name:
        return GAME_STATS.get('team_stats', {}).get(team_name, {})
    
    player_name = extract_player_name_from_query(query)  
    if player_name:
        print("the gotten player name")
        print(player_name)

        #do a search
        for team in GAME_STATS['player_stats'].keys():
            players = GAME_STATS['player_stats'][team]
            for player in players.keys():
                if player_name == player:
                    player_stats = players[player]
                    return player_stats
    
    print("returning no relevance")
    return "No relevant game stats found for this query."


def query_game_stats_summed(query):
    print("calling summed")
    player_name = extract_player_name_from_query(query)  
    print("the gotten player name")
    print(player_name)
    if player_name:
        player_stats = SUMMED_STATS.get(player_name, {})
        return player_stats if player_stats else "Player not found"
    
    team_name = extract_team_name_from_query(query, [game_info['team1'], game_info['team2']])  
    print("the gotten team name")
    print(team_name)
    if team_name:
        for k in GAME_STATS['team_stats'].keys():
            if k == team_name:
                team_stats = GAME_STATS['team_stats'][k]
                combined = {}
                for inner in team_stats.values():
                    for key, value in inner.items():
                        combined[key] = combined.get(key, 0) + value

                # recalculate percentages 
                combined["field_goal_percentage"] = (combined["made_field_goals"] / combined["attempted_field_goals"]) * 100 
                combined["three_point_percentage"] = (combined["made_three_pointers"] / combined["attempted_three_pointers"]) * 100
                combined["three_point_percentage"] = (combined["made_free_throws"] / combined["attempted_free_throws"]) * 100
                # print(json.dumps(combined, indent=4))

                return combined

    
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
    description="Use this tool to get quarter information on the current game about the whole team or a specific player",
    func=query_game_stats
)

summed_context_tool = Tool(
    name="CurrentgameSummed",
    description="Use this to get whole game information/context about the current team and players in the current game",
    func=query_game_stats_summed
)

tools = [ summed_context_tool, context_tool]

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

thelist = list(agent_executor.stream({"input": "Cleveland Cavaliers first quarter shooting percentage"}))
print(thelist[-1]['output'])

thelist = list(agent_executor.stream({"input": "Evan Mobley rebounding stats"}))
print(thelist[-1]['output'])

thelist = list(agent_executor.stream({"input": "Darius Garland field goal percentage"}))
print(thelist[-1]['output'])

thelist = list(agent_executor.stream({"input": "Cleveland Cavaliers first quarter turnover percentage"}))
print(thelist[-1]['output'])

thelist = list(agent_executor.stream({"input": "Evan Mobley defensive rebounds"}))
print(thelist[-1]['output'])