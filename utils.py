import json
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()
open_ai_key = os.getenv("OPENAI_APIKEY")
serp_api_key = os.getenv("SERP_APIKEY")

openai_client = OpenAI(
  api_key=open_ai_key,
)

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

def generate_queries_with_gpt(key_moments, game_info, context):
    prompt = (
        f"We are watching a live NBA game between {game_info['team1']} and {game_info['team2']}. Here is some context about the game: {context}\n\n"
        f"Here are the most recent key moments from the game:\n\n"
    )

    key_moment_str = ""

    for moment in key_moments:
        key_moment_str += f"{moment['time']}: {moment['description']} (Event: {moment['event']})\n"

    prompt += key_moment_str
    instruction = (
        "\nBased on these key moments, please generate 3-5 stat-driven queries that focus on historical comparisons, "
        "team trends, and notable player achievements in past games. Avoid hypothetical or predictive questions. "
        "The queries should be actionable and reflect a broader understanding of NBA stats and trends. "
        "Include queries about the game so far and comparisons to prior games this season or previous seasons."
        "This is a playoff game, frame your query around that."
        "Avoid 'how' based qualitative questions and generate quantifiable queries that can be answered with statistical data."
        "Make the queries specific, avoid general trend comparisons. Specify clear stats or metrics and get creative with them."
        "Avoid any trailing or leading text in your ouput and just output the queries."
    )
    prompt += instruction

    system_prompt = """
        Your output must be list of JSON objects. Each JSON object should contain two keys: "query" and "type".
        The "query" key should contain the generated query string, and the "type" key should indicate the type of query it is.
        The "type" can be one of the following: "team" for team-related queries, "player" for player-related queries, or "game" for game-related queries.
        An example of the output format is:
        [
            {"query": "What was the highest scoring game for the Boston Celtics in the 2021-22 season?", "type": "team"},
            {"query": "How many points did Jayson Tatum score in the last game against the Orlando Magic?", "type": "player"},
            {"query": "What was the final score of the last game between the Boston Celtics and Orlando Magic?", "type": "game"}
        ]
    """

    

    completion = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
    )


    return completion.choices[0].message.content


