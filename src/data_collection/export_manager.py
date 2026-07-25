"""
export_manager.py - Data export module for ML WebCrawler

This module handles parsing and compiling in-memory structures for database tracking:
- Exporting player information
- Exporting song information
- Exporting round information
"""

from data_collection.objects import Player

_cached_songs_array = []

def get_song(song_id: str) -> dict:
    """
    Retrieve a song by its ID from the active in-memory cache list.
    """
    global _cached_songs_array
    
    try:
        song = [s for s in _cached_songs_array if s.get('id') == song_id][0]
        if song:
            return song
    except IndexError:
        print(f"Could not find song with id {song_id}")
        raise

def export_players(rounds: list, current_avatars_cache: dict) -> list:
    """
    Export and compute player statistics dynamically from your memory records.
    
    Args:
        rounds (list): List of round dictionary structures.
        current_avatars_cache (dict): In-memory avatar dictionary mapping player_name -> avatar_url
        
    Returns:
        list: Sorted list of player analytics dictionaries.
    """
    players = []
    
    for round_obj in rounds:
        if hasattr(round_obj, "__dict__"):
            round_obj = round_obj.__dict__
        
        for song in round_obj.get("submissions", []):
            if isinstance(song, str):
                song = get_song(song)
            elif hasattr(song, "__dict__"):
                song = song.__dict__
            
            player_name = song.get("player_name", "Unknown")
            song_votes = song.get("votes", 0)
            
            existing_player = next((p for p in players if p["name"] == player_name), None)
            
            if not existing_player:
                avatar_url = current_avatars_cache.get(player_name, "")
                
                players.append({
                    "name": player_name,
                    "votes_to": song_votes,
                    "wins": 0,
                    "avatar": avatar_url
                })
            else:
                existing_player["votes_to"] += song_votes
        
        for name in round_obj.get("winner", []):
            winner = next((p for p in players if p["name"] == name), None)
            if winner:
                winner["wins"] += 1
    
    players = sorted(players, key=lambda x: x["name"])
    return players

def export_songs(rounds: list) -> list:
    """
    Export song datasets from rounds, assigning unique IDs for indexing.
    """
    global _cached_songs_array
    all_songs = []
    
    for round_obj in rounds:
        song_number = 1
        if hasattr(round_obj, "__dict__"):
            round_obj = round_obj.__dict__
        
        for song in round_obj.get("submissions", []):
            if isinstance(song, str):
                song = get_song(song)
            elif hasattr(song, "__dict__"):
                song = song.__dict__
            
            voters_list = song.get("voters", [])
            if voters_list and not isinstance(voters_list[0], dict):    
                song["voters"] = [vars(voter) if hasattr(voter, "__dict__") else voter for voter in voters_list]
            
            song["id"] = f"{song['player_name'][:3].lower()}{song_number:02d}{round_obj['round_number']:02d}"
            all_songs.append(song)
            song_number += 1
            
    _cached_songs_array = sorted(all_songs, key=lambda x: (x["player_name"], -x["votes"]))
    return _cached_songs_array

def export_rounds(rounds: list, current_avatars_cache: dict) -> list:
    """
    Compiles standard rounds data frames, extracting and processing child caches.
    """
    export_songs(rounds)
    export_players(rounds, current_avatars_cache)
    
    results = []
    
    for round_obj in rounds:
        if hasattr(round_obj, "__dict__"):
            round_obj = round_obj.__dict__
        
        songs_list = []
        song_number = 1
        
        for song in round_obj.get("submissions", []):
            if not isinstance(song, str):
                s_name = song.get("player_name", "unk") if isinstance(song, dict) else song.player_name
                song_id = f"{s_name[:3].lower()}{song_number:02d}{round_obj['round_number']:02d}"
                songs_list.append(song_id)
            else:
                songs_list.append(song)
            song_number += 1
        
        if songs_list:
            round_obj["submissions"] = songs_list
        
        results.append(round_obj)
        
    return results