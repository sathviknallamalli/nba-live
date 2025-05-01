import json

#load json
with open('game_stats.json', 'r') as f:
    gamestats  = json.load(f)

p1 = list(gamestats['player_stats']['Memphis Grizzlies'].keys())
p2 = list(gamestats['player_stats']['Oklahoma City Thunder'].keys())

print(p2)