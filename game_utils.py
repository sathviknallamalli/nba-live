import json
import re
from collections import defaultdict
import spacy
import copy
nlp = spacy.load("en_core_web_sm")


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
    elif "COACH'S CHALLENGE" in play_text:
        team = play_text.split()[1].replace("[", "").replace("]", "")
        return_obj = {"shot_type": "challenge", "team": team}
    elif "REVIEW" in play_text:
        team = play_text.split()[1].replace("[", "").replace("]", "")
        return_obj = {"shot_type": "review", "team": team}
    elif "kicked ball violation" in play_text:
        violator = play_text.split(" kicked")[0]
        return_obj = {"shot_type": "kicked_ball_violation", "violator": violator}
    elif "offensive charge" in play_text:
        charger = play_text.split(" offensive charge")[0]
        return_obj = {"shot_type": "charge", "charger": charger}
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
    elif "out of bounds bad pass" in play_text or "out of bounds lost ball" in play_text:
        player_name = play_text.split()[0] + " " + play_text.split()[1]
        return_obj = {"shot_type": "turnover", "turnover_player": player_name}
    elif "bad pass" in play_text:
        passer = play_text.split(" bad pass")[0].strip()
        return_obj = {"shot_type": "bad_pass", "passer": passer}
    elif "turnover" in play_text and "steals" in play_text:
        stealer = play_text.split(" steals")[0].split("(")[-1].strip()
        turnover_player = play_text.split("lost ball turnover")[0].strip()
        return_obj = {"shot_type": "turnover_steal", "turnover_player": turnover_player, "stealer": stealer}
    elif "turnover" in play_text:
        turnover_player = (play_text.split()[0] + " " + play_text.split()[1]).strip()
        return_obj = {"shot_type": "turnover", "turnover_player": turnover_player}
    elif "delay" in play_text:
        team = play_text.split(" delay")[0]
        return_obj = {"shot_type": "delay", "team": team}

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
    

def extract_player_name_from_query(query):
    # name_pattern = r"([A-Z][a-z]+ [A-Z][a-z]+)"
    # matches = re.findall(name_pattern, query)
    
    # if matches:
    #     return matches[0]
    
    # return None

    doc = nlp(query)
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            return ent.text
    return None

def extract_team_name_from_query(query, known_teams):
    query_lower = query.lower()    
    for team in known_teams:
        if team.lower() in query_lower:
            return team  # Return the first matched team name
    
    return None


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
                "bad_passes": 0,
                "attempted_field_goals": 0,
                "made_field_goals": 0,
                "attempted_three_pointers": 0,
                "made_three_pointers": 0,
                "attempted_free_throws": 0,
                "made_free_throws": 0,
                "field_goal_percentage": 0,
                "three_point_percentage": 0,
                "free_throw_percentage": 0,
                "delays": 0,
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
                "bad_passes": 0,
                "attempted_field_goals": 0,
                "made_field_goals": 0,
                "attempted_three_pointers": 0,
                "made_three_pointers": 0,
                "attempted_free_throws": 0,
                "made_free_throws": 0,
                "field_goal_percentage": 0,
                "three_point_percentage": 0,
                "free_throw_percentage": 0,
                "delays": 0,
            }),
        },
        "player_stats": defaultdict(lambda: defaultdict(lambda: {
            "1":{
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
            },
            "2":{
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
            },
            "3":{
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
            },
            "4":{
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
            }
            
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