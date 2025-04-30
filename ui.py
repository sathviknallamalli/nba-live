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


with open('./teams.json', 'r') as file:
    id_to_team = json.load(file)

# Global list to store incoming messages
incoming_messages = []
query_output = []
chat_messages = []

# WebSocket instance (to allow sending messages from the UI)
ws_instance = None

load_dotenv()
open_ai_key = os.getenv("OPENAI_APIKEY")
serp_api_key = os.getenv("SERP_APIKEY")

openai_client = OpenAI(
  api_key=open_ai_key,
)


def query_game_stats(query):
    print("calling the query game stats funciton")
    team_name = extract_team_name_from_query(query, [game_info['team1'], game_info['team2']])  
    if team_name:
        return GAME_STATS.get('team_stats', {}).get(team_name, {})
    
    player_name = extract_player_name_from_query(query)  
    if player_name:

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
    if player_name:
        player_stats = SUMMED_STATS.get(player_name, {})
        return player_stats if player_stats else "Player not found"
    
    team_name = extract_team_name_from_query(query, [game_info['team1'], game_info['team2']])  
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

                return combined
    
    return "No relevant game stats found for this query."

def search_statmuse(query: str) -> str:
  URL = f'https://www.statmuse.com/nba/ask/{query}'
  page = requests.get(URL)
  
  soup = BeautifulSoup(page.content, "html.parser")
  return soup.find("div", class_="flex flex-col justify-between @lg/hero:items-start").text

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

tools = [ summed_context_tool, context_tool, statmuse_tool, serpapi_tool]

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

#----START HERE ----
game_id = 401768035
game_url = f"https://www.espn.com/nba/playbyplay/_/gameId/{game_id}"
game_info = {
    'team1': 'Cleveland Cavaliers', #home
    'team2': 'Miami Heat', #away
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
    callback for messages received by the websocket
    """
    global incoming_messages
    global query_output
    global GAME_STATS
    global SUMMED_STATS
    data = json.loads(message)

    if data.get("op") == "C" and data.get("rc") == 200:
        #send the S messages for init
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
                
                #decrypt
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
                                # print(count_to_id)
                                print(play_text)
                                
                                print("og play doesnt exist to replace")
                                return
                            
                        if play_occur:
                            global current_window_of_plays
                            if play_id not in current_window_of_plays and "End of" not in play_text:
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

                                compound_queries = json.loads(generate_queries_with_gpt(key_moments_agg, game_info))


                                # compound_queries = compound_queries.strip().split('\n')
                                # compound_queries = [q.strip() for q in compound_queries if q.strip()]
                                # compound_queries = [re.sub(r'^\d+\.\s*', '', q.strip()) for q in compound_queries if q.strip()]

                                for cq in compound_queries:
                                    query = cq["query"]
                                    query_type = cq["type"]
                                    # print("---QUERY: " + cq)
                                    thelist = list(agent_executor.stream({"input": query}))
                                    # print("----ANSWER---- " + thelist[-1]['output'])
                                    print(thelist[-1]['output'])
                                    print("------------------------------------------------------------------")

                                    #remove sentences that starts with "i couldnt"
                                    #break into sentences
                                    sentences = thelist[-1]['output'].split('. ')
                                    sentences = [s for s in sentences if not s.startswith("I couldn't")]
                                    thelist[-1]['output'] = '. '.join(sentences)


                                    query_output.append(thelist[-1]['output'])
                                    running_list.delete(1.0, tk.END)
                                    running_list.insert(tk.END, "\n\n".join(query_output))  # Show last 20 messages
                                    running_list.see(tk.END)
                        
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

        incoming_messages.append("----GAME STARTED----")

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
        print("calling build")
        GAME_STATS, SUMMED_STATS = build_game_stats(raw_all_plays, GAME_STATS,SUMMED_STATS, game_info['team1'], game_info['team2'])
        # print(GAME_STATS['team_stats'].keys())
        # print(GAME_STATS['player_stats'].keys())
        # print(json.dumps(SUMMED_STATS, indent=4))

        #export the gamestats json
        with open('game_stats.json', 'w') as f:
            json.dump(GAME_STATS, f, indent=4)

        with open('summed_stats.json', 'w') as f:
            json.dump(SUMMED_STATS, f, indent=4)

        # display the UI for the summed stats
        for player in SUMMED_STATS:
            statlist = [player, SUMMED_STATS[player]["points"],
                        SUMMED_STATS[player]["rebounds"],
                        SUMMED_STATS[player]["assists"],
                        SUMMED_STATS[player]["turnovers"],
                        str(SUMMED_STATS[player]["two_pointers_made"]) + "-" + str(SUMMED_STATS[player]["two_pointers_attempted"]),
                        str(SUMMED_STATS[player]["three_pointers_made"] )+ "-" + str(SUMMED_STATS[player]["three_pointers_attempted"]),
                        str(SUMMED_STATS[player]["free_throws_made"]) + "-" + str(SUMMED_STATS[player]["free_throws_attempted"]),
                        str(round(SUMMED_STATS[player]["field_goal_percentage"] * 100, 2)),
                        str(round(SUMMED_STATS[player]["three_point_percentage"] * 100, 2)),
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
    # Launch the WebSocket listener in a separate thread.
    # ws_uri = "wss://echo.websocket.org"
    ws_uri = "wss://espn.connections.edge.bamgrid.com/66990c/connection?X-Application-Version=0.0.1&X-BAMSDK-Client-ID=espn-a9b93989&X-BAMSDK-Platform=javascript/macosx/chrome&X-BAMSDK-Version=27.1&X-Request-ID=&X-Request-Id=ec735d0f-b6f0-407f-9780-a2edde5b79ee"
    ws_thread = threading.Thread(target=start_websocket, args=(ws_uri,))
    ws_thread.daemon = True
    ws_thread.start()

def update_box_score():
    # Updates the Box Score panel with game stats data.
    global GAME_STATS
    # Clear the Treeview
    for row in box_score_tree.get_children():
        box_score_tree.delete(row)

    # Add game stats to the Treeview
    for team in GAME_STATS['player_stats'].keys():
        for player in GAME_STATS['player_stats'][team].keys():
            statlist = [player, GAME_STATS['player_stats'][team][player]["points"],
                        GAME_STATS['player_stats'][team][player]["rebounds"],
                        GAME_STATS['player_stats'][team][player]["assists"],
                        GAME_STATS['player_stats'][team][player]["turnovers"],
                        str(GAME_STATS['player_stats'][team][player]["two_pointers_made"]) + "-" + str(GAME_STATS['player_stats'][player]["two_pointers_attempted"]),
                        str(GAME_STATS['player_stats'][team][player]["three_pointers_made"] )+ "-" + str(GAME_STATS['player_stats'][player]["three_pointers_attempted"]),
                        str(GAME_STATS['player_stats'][team][player]["free_throws_made"]) + "-" + str(GAME_STATS['player_stats'][player]["free_throws_attempted"]),
                        str(round(GAME_STATS['player_stats'][team][player]["field_goal_percentage"] * 100, 2)),
                        str(round(GAME_STATS['player_stats'][team][player]["three_point_percentage"] * 100, 2)),
                        GAME_STATS['player_stats'][team][player]["defensive_rebounds"],
                        GAME_STATS['player_stats'][team][player]["offensive_rebounds"],
                        GAME_STATS['player_stats'][team][player]["charges_taken"],
                        GAME_STATS['player_stats'][team][player]["personal_fouls"],
                        GAME_STATS['player_stats'][team][player]["shots_blocked"],
                        GAME_STATS['player_stats'][team][player]["steals"]
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
# subtitle_label = tk.Label(title_frame, text=game_info['date'], font=("Arial", 14),fg=header_fg, bg=nba_blue)
# subtitle_label.grid(row=1, column=0, sticky="w", padx=10)

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
box_score_tree.column("Player", width=180)
box_score_tree.column("PTS", width=50)
box_score_tree.column("REB", width=50)
box_score_tree.column("AST", width=50)
box_score_tree.column("TO", width=50)
box_score_tree.column("2PT", width=50)
box_score_tree.column("3PT", width=50)
box_score_tree.column("FT", width=50)
box_score_tree.column("FG %", width=80)
box_score_tree.column("3PT %", width=80)
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
