f"""
cache_builder.py - Cloud-optimized Master Statistics Compiler

This module handles pre-computing the exhaustive personal statistics sub-tabs 
for every single player in a music league tournament session.
"""

from data_processing.search_processor import (
    find_top_songs, 
    find_songs_by_submitter, 
    find_player_songs_by_round, 
    get_votes_from_data
)
from data_processing.data_processor import process_player_stats

def build_static_dashboard_cache(payload: dict) -> dict:
    """
    Accepts raw structures directly from PostgreSQL data states, 
    pre-computes statistical tabs inside memory maps, and returns 
    a master dictionary payload ready for DB storage.
    """
    print("Starting containerized master stats pre-computation...")
    
    players = payload.get("players", [])
    username_mapping = payload.get("username_mapping", None)
        
    all_players_precomputed_stats = {}
    
    for player in players:
        if username_mapping:
            player["name"] = username_mapping.get(player.get("name"), player.get("name"))
        player_name = player.get("name")
        if not player_name:
            continue
            
        top_songs_data = find_top_songs(player_name) or []
        all_songs_data = find_songs_by_submitter(player_name) or []
        round_songs_data = find_player_songs_by_round(player_name) or []
        votes_data = get_votes_from_data(player_name) or {}

        remote_url = player.get("avatar")
        
        player_stats_data = process_player_stats(
            player, 
            top_songs_data, 
            all_songs_data,
            round_songs_data, 
            votes_data,
            username_mapping
        )
        
        player["num_comments"] = player_stats_data.get("comments", 0)
        
        player_stats_data["top_songs"] = top_songs_data or []
        player_stats_data["all_songs"] = all_songs_data or []
        player_stats_data["rounds_songs"] = round_songs_data or []
        player_stats_data["avatar_url"] = remote_url
        
        all_players_precomputed_stats[player_name] = player_stats_data

    if all_players_precomputed_stats:
        print(f"Success! Master stats matrix cache compiled entirely in memory.")
    else:
        print("Failed to process memory cache.")
    
    return {
        "players": players,
        "precomputed_stats": all_players_precomputed_stats
    }