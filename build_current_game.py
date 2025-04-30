
from game_utils import (
    parse_play_text
)

def build_game_stats(play_data, game_stats, summed_stats, hometeam, awayteam):
    def update_stats(play, stats, summed_stats, hometeam, awayteam):
        homeAway = play.get("homeAway")
        quarter = str(play["period"]["number"])

        if "shot clock" in play["text"]:
            return
        
        parsed_play = parse_play_text(play["text"])
        if parsed_play == {}:
            print("COULDNT PARSE THIS")
            print(play["text"])

        # print(parsed_play.keys())
        if(len(parsed_play.keys() ) == 0):
            return
        
        players_team = hometeam if homeAway == "home" else awayteam

        if "Chet Holmgren" in play["text"]:
            print(play["text"])
            print(players_team)
            print(parsed_play)
        
        if parsed_play['shot_type'] == "free_throw" or parsed_play['shot_type'] == "two_pointer" or parsed_play['shot_type'] == "three_pointer":
            points, scorer, shot_type = parsed_play.get("points"), parsed_play.get("scorer"), parsed_play.get("shot_type")
            
            #update team points
            if homeAway == "home":
                stats["team_stats"][hometeam][quarter]["points"] += points
            else:
                stats["team_stats"][awayteam][quarter]["points"] += points

            
            if scorer:
                
                stats["player_stats"][players_team][scorer][quarter]["points"] += points
                summed_stats[scorer]["points"] += points
                if shot_type == "two_pointer":
                    stats["player_stats"][players_team][scorer][quarter]["two_pointers_attempted"] += 1
                    stats["player_stats"][players_team][scorer][quarter]["two_pointers_made"] += 1 if points == 2 else 0
                    stats["player_stats"][players_team][scorer][quarter]["field_goal_percentage"] = float((stats["player_stats"][players_team][scorer][quarter]["two_pointers_made"] + stats["player_stats"][players_team][scorer][quarter]["three_pointers_made"]) / (stats["player_stats"][players_team][scorer][quarter]["two_pointers_attempted"] + stats["player_stats"][players_team][scorer][quarter]["three_pointers_attempted"]))
                    summed_stats[scorer]["two_pointers_attempted"] += 1
                    summed_stats[scorer]["two_pointers_made"] += 1 if points == 2 else 0
                    summed_stats[scorer]["field_goal_percentage"] = float((summed_stats[scorer]["two_pointers_made"] + summed_stats[scorer]["three_pointers_made"]) / (summed_stats[scorer]["two_pointers_attempted"] + summed_stats[scorer]["three_pointers_attempted"]))

                    theteam = hometeam if homeAway == "home" else awayteam
                    stats['team_stats'][theteam][quarter]['attempted_field_goals'] += 1
                    stats['team_stats'][theteam][quarter]['made_field_goals'] += 1 if points == 2 else 0
                    stats['team_stats'][theteam][quarter]['field_goal_percentage'] = float(stats['team_stats'][theteam][quarter]['made_field_goals'] / stats['team_stats'][theteam][quarter]['attempted_field_goals'])
                elif shot_type == "three_pointer":
                    
                    stats["player_stats"][players_team][scorer][quarter]["three_pointers_attempted"] += 1
                    stats["player_stats"][players_team][scorer][quarter]["three_pointers_made"] += 1 if points == 3 else 0
                    stats["player_stats"][players_team][scorer][quarter]["three_point_percentage"] = float(stats["player_stats"][players_team][scorer][quarter]["three_pointers_made"] / stats["player_stats"][players_team][scorer][quarter]["three_pointers_attempted"])
                    stats["player_stats"][players_team][scorer][quarter]["field_goal_percentage"] = float((stats["player_stats"][players_team][scorer][quarter]["two_pointers_made"] + stats["player_stats"][players_team][scorer][quarter]["three_pointers_made"]) / (stats["player_stats"][players_team][scorer][quarter]["two_pointers_attempted"] + stats["player_stats"][players_team][scorer][quarter]["three_pointers_attempted"]))
                    summed_stats[scorer]["three_pointers_attempted"] += 1
                    summed_stats[scorer]["three_pointers_made"] += 1 if points == 3 else 0
                    summed_stats[scorer]["three_point_percentage"] = float(summed_stats[scorer]["three_pointers_made"] / summed_stats[scorer]["three_pointers_attempted"])
                    summed_stats[scorer]["field_goal_percentage"] = float((summed_stats[scorer]["two_pointers_made"] + summed_stats[scorer]["three_pointers_made"]) / (summed_stats[scorer]["two_pointers_attempted"] + summed_stats[scorer]["three_pointers_attempted"]))

                    theteam = hometeam if homeAway == "home" else awayteam
                    stats['team_stats'][theteam][quarter]['attempted_three_pointers'] += 1
                    stats['team_stats'][theteam][quarter]['made_three_pointers'] += 1 if points == 3 else 0
                    stats['team_stats'][theteam][quarter]['three_point_percentage'] = float(stats['team_stats'][theteam][quarter]['made_three_pointers'] / stats['team_stats'][theteam][quarter]['attempted_three_pointers'])
                elif shot_type == "free_throw":
                    stats["player_stats"][players_team][scorer][quarter]["free_throws_attempted"] += 1
                    stats["player_stats"][players_team][scorer][quarter]["free_throws_made"] += 1 if points == 1 else 0
                    summed_stats[scorer]["free_throws_attempted"] += 1
                    summed_stats[scorer]["free_throws_made"] += 1 if points == 1 else 0

                    theteam = hometeam if homeAway == "home" else awayteam
                    stats['team_stats'][theteam][quarter]['attempted_free_throws'] += 1
                    stats['team_stats'][theteam][quarter]['made_free_throws'] += 1 if points == 1 else 0
                    stats['team_stats'][theteam][quarter]['free_throw_percentage'] = float(stats['team_stats'][theteam][quarter]['made_free_throws'] / stats['team_stats'][theteam][quarter]['attempted_free_throws'])
        elif parsed_play['shot_type'] == "blocked_shot":
            blocker, shooter = parsed_play.get("blocker"), parsed_play.get("shooter")
            other_team = awayteam if players_team == hometeam else hometeam
            stats["player_stats"][other_team][blocker][quarter]["shots_blocked"] += 1
            stats["player_stats"][players_team][shooter][quarter]["own_shots_have_been_blocked"] += 1
            stats["player_stats"][players_team][shooter][quarter]["two_pointers_attempted"] += 1
            summed_stats[blocker]["shots_blocked"] += 1
            summed_stats[shooter]["own_shots_have_been_blocked"] += 1
            summed_stats[shooter]["two_pointers_attempted"] += 1

        elif parsed_play['shot_type'] == "rebound_defensive":
            rebounder = parsed_play.get("rebounder")
            stats["player_stats"][players_team][rebounder][quarter]["defensive_rebounds"] += 1
            summed_stats[rebounder]["defensive_rebounds"] += 1

            theteam = hometeam if homeAway == "home" else awayteam
            stats["team_stats"][theteam][quarter]["defensive_rebounds"] += 1
        elif parsed_play['shot_type'] == "rebound_offensive":
            rebounder = parsed_play.get("rebounder")
            stats["player_stats"][players_team][rebounder][quarter]["offensive_rebounds"] += 1
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
            stats["player_stats"][players_team][shooter][quarter]["free_throws_attempted"] += 1
            stats["player_stats"][players_team][shooter][quarter]["free_throw_perctange"] = float(stats["player_stats"][players_team][shooter][quarter]["free_throws_made"] / stats["player_stats"][players_team][shooter][quarter]["free_throws_attempted"])
            summed_stats[shooter]["free_throws_attempted"] += 1
            summed_stats[shooter]["free_throw_perctange"] = float(summed_stats[shooter]["free_throws_made"] / summed_stats[shooter]["free_throws_attempted"])

            theteam = hometeam if homeAway == "home" else awayteam
            stats['team_stats'][theteam][quarter]['attempted_free_throws'] += 1
            stats['team_stats'][theteam][quarter]['free_throw_percentage'] = float(stats['team_stats'][theteam][quarter]['made_free_throws'] / stats['team_stats'][theteam][quarter]['attempted_free_throws'])
        elif parsed_play['shot_type'] == "missed_three_pointer":
            shooter = parsed_play.get("shooter")
            stats["player_stats"][players_team][shooter][quarter]["three_pointers_attempted"] += 1
            stats["player_stats"][players_team][shooter][quarter]["three_point_percentage"] = float(stats["player_stats"][players_team][shooter][quarter]["three_pointers_made"] / stats["player_stats"][players_team][shooter][quarter]["three_pointers_attempted"])
            stats["player_stats"][players_team][shooter][quarter]["field_goal_percentage"] = float((stats["player_stats"][players_team][shooter][quarter]["two_pointers_made"] + stats["player_stats"][players_team][shooter][quarter]["three_pointers_made"]) / (stats["player_stats"][players_team][shooter][quarter]["two_pointers_attempted"] + stats["player_stats"][players_team][shooter][quarter]["three_pointers_attempted"]))
            summed_stats[shooter]["three_pointers_attempted"] += 1
            summed_stats[shooter]["three_point_percentage"] = float(summed_stats[shooter]["three_pointers_made"] / summed_stats[shooter]["three_pointers_attempted"])
            summed_stats[shooter]["field_goal_percentage"] = float((summed_stats[shooter]["two_pointers_made"] + summed_stats[shooter]["three_pointers_made"]) / (summed_stats[shooter]["two_pointers_attempted"] + summed_stats[shooter]["three_pointers_attempted"]))

            theteam = hometeam if homeAway == "home" else awayteam
            stats['team_stats'][theteam][quarter]['attempted_three_pointers'] += 1
            stats['team_stats'][theteam][quarter]['three_point_percentage'] = float(stats['team_stats'][theteam][quarter]['made_three_pointers'] / stats['team_stats'][theteam][quarter]['attempted_three_pointers'])
        elif parsed_play['shot_type'] == "missed_two_pointer":
            shooter = parsed_play.get("shooter")
            stats["player_stats"][players_team][shooter][quarter]["two_pointers_attempted"] += 1
            stats["player_stats"][players_team][shooter][quarter]["field_goal_percentage"] = float((stats["player_stats"][players_team][shooter][quarter]["two_pointers_made"] + stats["player_stats"][players_team][shooter][quarter]["three_pointers_made"]) / (stats["player_stats"][players_team][shooter][quarter]["two_pointers_attempted"] + stats["player_stats"][players_team][shooter][quarter]["three_pointers_attempted"]))
            summed_stats[shooter]["two_pointers_attempted"] += 1
            summed_stats[shooter]["field_goal_percentage"] = float((summed_stats[shooter]["two_pointers_made"] + summed_stats[shooter]["three_pointers_made"]) / (summed_stats[shooter]["two_pointers_attempted"] + summed_stats[shooter]["three_pointers_attempted"]))

            theteam = hometeam if homeAway == "home" else awayteam
            stats['team_stats'][theteam][quarter]['attempted_field_goals'] += 1
            stats['team_stats'][theteam][quarter]['field_goal_percentage'] = float(stats['team_stats'][theteam][quarter]['made_field_goals'] / stats['team_stats'][theteam][quarter]['attempted_field_goals'])
        elif parsed_play['shot_type'] == "charge":
            charger = parsed_play.get("charger")
            stats["player_stats"][players_team][charger][quarter]["charges_taken"] += 1
            summed_stats[charger]["charges_taken"] += 1
        elif parsed_play['shot_type'] == "personal_foul":
            fouler = parsed_play.get("fouler")
            stats["player_stats"][players_team][fouler][quarter]["personal_fouls"] += 1
            summed_stats[fouler]["personal_fouls"] += 1
        elif parsed_play['shot_type'] == 'shooting_foul':
            fouler = parsed_play.get("fouler")
            stats["player_stats"][players_team][fouler][quarter]["shooting_fouls"] += 1
            summed_stats[fouler]["shooting_fouls"] += 1
        elif parsed_play['shot_type'] == 'loose_ball_foul':
            fouler = parsed_play.get("fouler")
            stats["player_stats"][players_team][fouler][quarter]["loose_ball_foul"] += 1
            summed_stats[fouler]["loose_ball_foul"] += 1
        elif parsed_play['shot_type'] == 'steal':
            stealer = parsed_play.get("stealer")
            passer = parsed_play.get("passer")
            other_team = awayteam if players_team == hometeam else hometeam

            stats["player_stats"][other_team][stealer][quarter]["steals"] += 1
            stats["player_stats"][players_team][passer][quarter]["bad_passes"] += 1
            stats["team_stats"][players_team][quarter]["bad_passes"] += 1
            summed_stats[stealer]["steals"] += 1
            summed_stats[passer]["bad_passes"] += 1
        elif parsed_play['shot_type'] == 'bad_pass':
            passer = parsed_play.get("passer")
            stats["player_stats"][players_team][passer][quarter]["bad_passes"] += 1
            summed_stats[passer]["bad_passes"] += 1
            if homeAway == "home":
                stats["team_stats"][hometeam][quarter]["turnovers"] += 1
            else:
                stats["team_stats"][awayteam][quarter]["turnovers"] += 1
        elif parsed_play['shot_type'] == 'turnover_steal':
            turnover_player = parsed_play.get("turnover_player")
            stealer = parsed_play.get("stealer")
            stats["player_stats"][players_team][turnover_player][quarter]["turnovers"] += 1
            other_team = awayteam if players_team == hometeam else hometeam
            stats["player_stats"][other_team][stealer][quarter]["steals"] += 1
            summed_stats[turnover_player]["turnovers"] += 1
            summed_stats[stealer]["steals"] += 1
            if homeAway == "home":
                stats["team_stats"][hometeam][quarter]["turnovers"] += 1
            else:
                stats["team_stats"][awayteam][quarter]["turnovers"] += 1
        elif parsed_play['shot_type'] == 'turnover':
            turnover_player = parsed_play.get("turnover_player")
            stats["player_stats"][players_team][turnover_player][quarter]["turnovers"] += 1
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
            stats["player_stats"][players_team][violator][quarter]["personal_fouls"] += 1
            summed_stats[violator]["personal_fouls"] += 1
        elif parsed_play['shot_type'] == 'goaltending':
            goaltender = parsed_play.get("goaltender")
            stats["player_stats"][players_team][goaltender][quarter]["goaltending_calls"] += 1
            summed_stats[goaltender]["goaltending_calls"] += 1
        elif parsed_play['shot_type'] == 'delay':
            if homeAway == "home":
                stats["team_stats"][hometeam][quarter]["delays"] += 1
            else:
                stats["team_stats"][awayteam][quarter]["delays"] += 1
        elif parsed_play['shot_type'] == 'challenge':
            pass
        elif parsed_play['shot_type'] == 'review':
            pass

        if "assister" in parsed_play:
            assister = parsed_play.get("assister")
            stats["player_stats"][players_team][assister][quarter]["assists"] += 1
            summed_stats[assister]["assists"] += 1
            if homeAway == "home":
                stats["team_stats"][hometeam][quarter]["assists"] += 1
            else:
                stats["team_stats"][awayteam][quarter]["assists"] += 1


    for play in play_data:
        update_stats(play, game_stats, summed_stats, hometeam, awayteam)

    return game_stats, summed_stats
