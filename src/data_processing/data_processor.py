import datetime
from data_processing.cache_manager import read_json, write_json
from data_processing.search_processor import get_players, get_rounds, get_songs, find_song_by_id, find_songs_by_submitter, find_player_songs_by_round

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
            key=lambda item: item.get("wins", 0) if isinstance(item, dict) else 0, 
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
            key=lambda item: item.get("num_comments", 0) if isinstance(item, dict) else 0, 
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

def prepare_master_matrix():
    data = []
    players_data = get_players() or []
    
    for player in players_data:
        row = []
        player_name = player.get("name", "Unknown")
        if player_name and player_name != "[Left the league]":
        
            stats_profile = read_json(f"precomputed_stats_{player_name}") or {}
            votes = stats_profile.get("votes_from_data", {}).copy()
            
            votes[player_name] = 0
            sorted_votes = sorted(votes.items(), key=lambda x: x[0])
            
            row.append(player_name)
            for target_player, vote_count in sorted_votes:
                row.append(vote_count)
        data.append(row)

    return data

def prepare_player_round_info(player):
    data = []
    rounds = get_rounds() or []
    songs = find_songs_by_submitter(player) or []

    for round_obj in rounds:
        round_data = {}
        round_number = round_obj.get('round_number')
        
        round_data[round_number] = {
            "title": round_obj.get("title", f"Round {round_number}"),
            "songs": []
        }
        for song in songs:
            if song.get("id") in round_obj.get("submissions", []):
                round_data[round_number]["songs"].append(song)
        data.append(round_data)
    return data

def process_player_stats(player: dict, top_songs_data: list, all_songs_data: list, round_songs_data: dict, votes_data: dict):
    """
    Precomputes dynamic statistics variables, verifying list/dict indices inside container loops.
    """
    data = {}
    top_votes = 0
    total_votes_given = 0
    times_voted = 0

    data["comments"] = 0
    data["votes_from_data"] = votes_data.get("votes_from_data", {})
    data["votes_songs"] = votes_data.get("votes_songs", {})
    
    votes_to_map = votes_data.get("votes_to_data", {})
    for op, votes in votes_to_map.items():
        if int(votes) > top_votes:
            top_votes = int(votes)
            data["favorite_player"] = op
        total_votes_given += int(votes) 

    top_players = {}
    for song_id in top_songs_data:
        song = find_song_by_id(song_id)
        if song and "player_name" in song:
            p_submitter = song["player_name"]
            top_players[p_submitter] = top_players.get(p_submitter, 0) + 1
            
    if top_players:       
        data["top_player"] = sorted(top_players.keys(), key=lambda x: x)[0]

    best_round_score = 0
    if isinstance(round_songs_data, dict):
        iterations = round_songs_data.values()
    else:
        iterations = round_songs_data if round_songs_data else []

    for round_item in iterations:
        if isinstance(round_item, dict) and round_item.get("songs"):
            round_total = 0
            for song_id in round_item["songs"]:
                song = find_song_by_id(song_id)
                if song:
                    round_total += song.get("votes", 0)
            if round_total > best_round_score:
                best_round_score = round_total
                data["best_round"] = round_item
                data["best_round"]["score"] = best_round_score

    player_artists = {}
    best_song_score = 0
    for song_id in all_songs_data:
        song = find_song_by_id(song_id)
        if not song:
            continue
            
        if song.get("votes", 0) > best_song_score:
            best_song_score = song.get("votes", 0) 
            data["best_song"] = song_id
            
        artist = song.get("artist", "Unknown Artist")
        if artist not in player_artists:
            player_artists[artist] = {
                "songs": [song],
                "appearances": 1,
                "votes": song.get("votes", 0)
            }
        else:
            player_artists[artist]["appearances"] += 1
            player_artists[artist]["songs"].append(song)
            player_artists[artist]["votes"] += song.get("votes", 0)

    for song in get_songs() or []:
        voters = song.get("voters", [])
        for voter in voters:
            if voter.get("name") == player.get("name"):
                if int(voter.get("votes", 0)) > 0:
                    times_voted += 1
                    if voter.get("comment"):data["comments"] += 1
                    if player_artists:data["favorite_artist"] = sorted(player_artists.items(), key=lambda x: x[1]["appearances"], reverse=True)[0]
                    data["top_artist"] = sorted(player_artists.items(), key=lambda x: x[1]["votes"], reverse=True)[0]
                    if times_voted > 0:
                        data["points_per_vote"] = round(float(total_votes_given / times_voted), 2)
    return data