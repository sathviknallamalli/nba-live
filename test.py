
import requests
from bs4 import BeautifulSoup
import urllib.request
import json
from collections import defaultdict

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

def current_game_data(game_id):
    url = f"https://www.espn.com/nba/boxscore/_/gameId/{game_id}"
    with urllib.request.urlopen(url) as response:
        html = response.read()

    soup = BeautifulSoup(html, 'html.parser')
    main_div = soup.find_all('div', class_='Wrapper')

    both_team_data = []

    for d in main_div:
        nested_divs = d.find("div")
        if len(nested_divs) == 1:
            divs_to_check = nested_divs.find("div")
            for div in divs_to_check:
                flex_div = div.find("div", class_="flex")
                # print(flex_div)
                
                if flex_div != None:
                    left_table = flex_div.find("table", class_="Table Table--align-right Table--fixed Table--fixed-left")
                    left_map = parse_table(left_table)

                    right_table = flex_div.find("table", class_="Table Table--align-right")
                    right_map = parse_table(right_table)

                    table_map = {}
                    for key in left_map:
                        table_map[left_map[key][0]]=  right_map[key]
                    
                    stat_names = table_map['starters']
                    del table_map['bench']
                    del table_map['starters']
                    del table_map['']
                    for key in table_map:
                        if len(table_map[key]) > 1:
                            raw_vals = table_map[key]
                            newdict = {}
                            for i in range(len(stat_names)):
                                newdict[stat_names[i]] = raw_vals[i]
                            table_map[key] = newdict
                    both_team_data.append(table_map)

    return both_team_data



team = "home"
awayteam = "away"
initial_game_state = {
        "team_stats": {
            team: defaultdict(lambda: {
                "points": 0,
                "rebounds": 0,
                "assists": 0,
                "turnovers": 0,
                "blocks": 0,
                "steals": 0,
                "offensive_rebounds": 0,
                "defensive_rebounds": 0,
                "field_goals_made": 0,
                "field_goals_attempted": 0,
                "three_points_made": 0,
                "three_points_attempted": 0,
                "personal_fouls": 0,
                "free_throws_made": 0,
                "free_throws_attempted": 0,

            }),
            awayteam: defaultdict(lambda: {
                "points": 0,
                "rebounds": 0,
                "assists": 0,
                "turnovers": 0,
                "blocks": 0,
                "steals": 0,
                "offensive_rebounds": 0,
                "defensive_rebounds": 0,
                "field_goals_made": 0,
                "field_goals_attempted": 0,
                "three_points_made": 0,
                "three_points_attempted": 0,
                "personal_fouls": 0,
                "free_throws_made": 0,
                "free_throws_attempted": 0,
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
            "shots_blocked": 0,
            "own_shots_have_been_blocked": 0,
            "defensive_rebounds": 0,
            "offensive_rebounds": 0,
            "charges_taken": 0,
            "personal_fouls": 0,
            "shooting_fouls": 0,
            "loose_ball_foul": 0,
            "steals": 0,
            "bad_passes": 0,
            "turnovers": 0,
        })),
}



def populate_game_stats(initial_game_state, scraped_data, team):
    # print(scraped_data.keys())
    for player in scraped_data.keys():
        print(json.dumps(scraped_data[player], indent=4))
        break

    initial_game_state["team_stats"][team]["points"] = scraped_data['team']['PTS']
    initial_game_state["team_stats"][team]["rebounds"] = scraped_data['team']['REB']
    initial_game_state["team_stats"][team]["assists"] = scraped_data['team']['AST']
    initial_game_state["team_stats"][team]["turnovers"] = scraped_data['team']['TO']
    initial_game_state["team_stats"][team]["blocks"] = scraped_data['team']['BLK']
    initial_game_state["team_stats"][team]["steals"] = scraped_data['team']['STL']
    initial_game_state["team_stats"][team]["offensive_rebounds"] = scraped_data['team']['OREB']
    initial_game_state["team_stats"][team]["defensive_rebounds"] = scraped_data['team']['DREB']

    field_goals = scraped_data['team']['FG']
    initial_game_state["team_stats"][team]["field_goals_made"] = field_goals.split('-')[0]
    initial_game_state["team_stats"][team]["field_goals_attempted"] = field_goals.split('-')[1]

    three_pointers = scraped_data['team']['3PT']
    initial_game_state["team_stats"][team]["three_points_made"] = three_pointers.split('-')[0]
    initial_game_state["team_stats"][team]["three_points_attempted"] = three_pointers.split('-')[1]

    free_throws = scraped_data['team']['FT']
    initial_game_state["team_stats"][team]["free_throws_made"] = free_throws.split('-')[0]
    initial_game_state["team_stats"][team]["free_throws_attempted"] = free_throws.split('-')[1]

    initial_game_state["team_stats"][team]["personal_fouls"] = scraped_data['team']['PF']

    return initial_game_state


both_team_data = current_game_data(401547678)
home_team = both_team_data[0]
away_team = both_team_data[1]
populate_game_stats(initial_game_state, home_team, team)
populate_game_stats(initial_game_state, away_team, awayteam)

# print(json.dumps(initial_game_state["team_stats"], indent=4))
