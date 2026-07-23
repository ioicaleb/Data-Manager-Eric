import datetime
from data_processing.json_manager import *
from data_processing.search_processor import *
from fastapi import FastAPI

app = FastAPI()

def process_standings_votes():
    processed_players = []
    data = []
    players_data = get_players()

    if isinstance(players_data, dict):
        sorted_players = sorted(
            players_data.items(), 
            key=lambda item: item[1].get("votes_to", 0) if isinstance(item[1], dict) else 0, 
            reverse=True
        )

        for key, value in sorted_players:
            if isinstance(value, dict):
                if "name" not in value:
                    value["name"] = key
                processed_players.append(value)

    elif isinstance(players_data, list):
        sorted_players = sorted(
            players_data, 
            key=lambda item: item.get("votes_to", 0) if isinstance(item, dict) else 0, 
            reverse=True
        )
        
        for item in sorted_players:
            if isinstance(item, dict):
                if "name" not in item:
                    item["name"] = item.get("player") or "Unknown Player"
                processed_players.append(item)
            
        current_position = 1
        previous_votes = None
        
        for index, player_info in enumerate(processed_players):
            name = player_info.get("name", "Unknown")
            votes = player_info.get("votes_to", 0)
            
            if previous_votes is not None and votes < previous_votes:
                current_position = index + 1
    
            player_info["position"] = f"#{current_position}"
                
            previous_votes = votes
            medal = "🥇 " if current_position == 1 else "🥈 " if current_position == 2 else "🥉 " if current_position == 3 else f" #{current_position} "
            
            data.append(f"{medal}{name} - Votes: {votes}")
        
        return data

def process_standings_wins():
    processed_players = []
    data = []
    players_data = get_players()

    if isinstance(players_data, dict):
        sorted_players = sorted(
            players_data.items(), 
            key=lambda item: item[1].get("wins", 0) if isinstance(item[1], dict) else 0, 
            reverse=True
        )

        for key, value in sorted_players:
            if isinstance(value, dict):
                if "name" not in value:
                    value["name"] = key
                processed_players.append(value)

    elif isinstance(players_data, list):
        sorted_players = sorted(
            players_data, 
            key=lambda item: item.get("wins") if isinstance(item, dict) else 0, 
            reverse=True
        )
        
        for item in sorted_players:
            if isinstance(item, dict):
                if "name" not in item:
                    item["name"] = item.get("player") or "Unknown Player"
                processed_players.append(item)
        
    current_position = 1
    previous_wins = None
    
    for index, player_info in enumerate(processed_players):
        name = player_info.get("name", "Unknown")
        wins = player_info.get("wins", 0)
        
        if previous_wins is not None and wins < previous_wins:
            current_position = index + 1

        standings_position = f"#{current_position}"
            
        previous_wins = wins
        medal = "🥇 " if current_position == 1 else "🥈 " if current_position == 2 else "🥉 " if current_position == 3 else f" {standings_position} "
        
        data.append(f"{medal}{name} - Wins: {wins}")
    
    return data

def process_standings_comments():
    processed_players = []
    data = []
    players_data = get_players()

    if isinstance(players_data, dict):
        sorted_players = sorted(
            players_data.items(), 
            key=lambda item: item[1].get("num_comments", 0) if isinstance(item[1], dict) else 0, 
            reverse=True
        )

        for key, value in sorted_players:
            if isinstance(value, dict):
                if "name" not in value:
                    value["name"] = key
                processed_players.append(value)

    elif isinstance(players_data, list):
        sorted_players = sorted(
            players_data, 
            key=lambda item: item.get("num_comments") if isinstance(item, dict) else 0, 
            reverse=True
        )
        
        for item in sorted_players:
            if isinstance(item, dict):
                if "name" not in item:
                    item["name"] = item.get("player") or "Unknown Player"
                processed_players.append(item)
        
    current_position = 1
    previous_comments = None
    
    for index, player_info in enumerate(processed_players):
        name = player_info.get("name", "Unknown")
        comments = player_info.get("num_comments", 0)
        
        if previous_comments is not None and comments < previous_comments:
            current_position = index + 1

        standings_position = f"#{current_position}"
            
        previous_comments = comments
        medal = "🥇 " if current_position == 1 else "🥈 " if current_position == 2 else "🥉 " if current_position == 3 else f" {standings_position} "
        
        data.append(f"{medal}{name} - Comments: {comments}")
    
    return data

def save_app_data():
    """Save the timestamp of when data was last collected"""
    current_time = datetime.datetime.now()
    app_data = {
        "date": current_time.isoformat()
    }
    write_json("app_data", app_data)

def prepare_master_matrix():
    data = []
    players_data = get_players()
    for player in players_data:
        row = []
        player_name = player.get("name")
        votes = read_json(f"precomputed_stats_{player.get('name', 'Unknown')}").get(player_name, {}).get("votes_from_data", {})
        votes[player_name] = 0
        votes = sorted(votes.items(), key = lambda x: x[0])
        row.append(player_name)
        for player, votes in votes:
            if player != "Lindsay" and player != "Magnolia":
                row.append(votes)
        data.append(row)

    return data

def prepare_player_round_info(player):
    data = []
    rounds = get_rounds()
    songs = find_songs_by_submitter(player)

    for round in rounds:
        round_data = {}
        round_id = round['round_number']
        round_data[round_id] = {
            "title": round["title"],
            "songs": []
        }
        for song in songs:
            if song["id"] in round["submissions"]:
                round_id["songs"].append(song)
        data.append(round_data)
    return data

def process_player_stats(player: dict, top_songs_data: dict, all_songs_data: dict, round_songs_data: dict, votes_data: dict):
    data = {}
    top_votes = 0
    total_votes_given = 0
    times_voted = 0

    data["comments"] = 0
    data["votes_from_data"] = votes_data["votes_from_data"]
    data["votes_songs"] = votes_data["votes_songs"]
    
    for op, votes in votes_data["votes_to_data"].items():
        if int(votes) > top_votes:
            top_votes = votes
            data["favorite_player"] = op
        total_votes_given += int(votes) 

    top_players = {}
    for song_id in top_songs_data:
        song = find_song_by_id(song_id)
        if song["player_name"] not in top_players.keys():
            top_players[song["player_name"]] = 1
        else:
            top_players[song["player_name"]] += 1
    if top_players:       
        data["top_player"] = sorted(top_players, key=lambda x: x)[0]

    best_round_score = 0
    for round_item in round_songs_data:
        if round_item.get("songs"):
            round_total = 0
            for song_id in round_item["songs"]:
                song = find_song_by_id(song_id)
                round_total += song.get("votes")
            if round_total > best_round_score:
                best_round_score = round_total
                data["best_round"] = round_item
                data["best_round"]["score"] = best_round_score

    player_artists = {}
    best_song_score = 0
    for song_id in all_songs_data:
        song = find_song_by_id(song_id)
        if(song.get("votes")) > best_song_score:
            data["best_song"] = song_id
        artist = song["artist"]
        if artist not in player_artists:
            player_artists[artist] = {
                "songs": [song,],
                "appearances": 1,
                "votes": 0
            }
            player_artists[artist]["votes"] += song["votes"]
        else:
            player_artists[artist]["appearances"] += 1
            player_artists[artist]["songs"].append(song)
            player_artists[artist]["votes"] += song["votes"]

    for song in get_songs():
        voters = song.get("voters")
        for voter in voters:
            if voter.get("name") == player.get("name"): 
                if int(voter.get("votes")) > 0:
                    times_voted += 1
                if voter["comment"]:
                    data["comments"] += 1

    if player_artists:
        data["favorite_artist"] = sorted(player_artists.items(), key=lambda x: x[1]["appearances"], reverse = True)[0]
        data["top_artist"] = sorted(player_artists.items(), key=lambda x: x[1]["votes"], reverse = True)[0]

    if times_voted > 0:
        data["points_per_vote"] = round(float(total_votes_given / times_voted), 2)

    return data