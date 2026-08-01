"""
data_collector.py - Main execution module for ML WebCrawler

This module serves as the entry point for the web crawler application,
handling the main workflow of fetching data, processing results,
and exporting database analytics states.
"""
from data_collection.web_crawler import get_results, load_avatar_cache, get_avatar_cache
from data_collection.objects import convert_username_to_name
from data_collection.export_manager import export_players, export_songs
from data_processing.cache_builder import build_static_dashboard_cache
from data_processing.cache_manager import initialize_memory_cache

songs = {}
players = {}
results = {}
config = {}

def run_pipeline_migration(league_id: str, browser_type: str, session_cookie: str, cached_db_data: dict) -> dict:
    global songs, players, results, config
    
    config = {
        "league_id": league_id,
        "browser_type": browser_type,
        "session_cookie": session_cookie,
        "username-player_name": cached_db_data.get("username_mapping", {})
    }
    
    load_avatar_cache(cached_db_data.get("avatars", {}))
    
    results = cached_db_data.get("rounds", [])
    songs = cached_db_data.get("songs", {})
    players = cached_db_data.get("players", {})

    if results and players and songs:
        print(f"Pulled previous results from database for league: {league_id}")
        initialize_memory_cache({
            "rounds": results,
            "songs": songs,
            "players": players
        })
        new_round_check(config)
    else:
        print("No valid parsed history found inside PostgreSQL. Initializing full Selenium scrape sequence...")
        
        scraped_rounds = get_results(config) 
        
        results = scraped_rounds

    return results

def process_results(username_mapping: dict) -> dict:
    global songs, players, results, config
    if not config.get("username-player_name"):
        config["username-player_name"] = username_mapping
    if not players:
        players = export_players(results, get_avatar_cache())
        for player in players:
            username = player.get("name", "")
            if username == "[Left the league]":
                players.remove(player)
            name = convert_username_to_name(username, username_mapping)
            player["name"] = name
    if not songs:
        converted_songs = []
        songs = export_songs(results)
        song_number = 1
        for song in songs:
            submitter = song.get("player_name", "")
            submitter_name = convert_username_to_name(submitter, username_mapping)
            song["id"] = f"{submitter_name[:3].lower()}{song.get("artist")[:3].lower()}{song.get("name")[:3].lower()}{song_number:05d}"
            song_number += 1
            for voter in song.get("voters", []):
                name = voter.get("name", "")
                voter_name = convert_username_to_name(name, username_mapping)
                voter["name"] = voter_name
            converted_songs.append({
                "id": song.get("id"),
                "name": song.get("name", "Unknown Title"),
                "artist": song.get("artist", "Unknown Artist"),
                "album": song.get("album", "Unknown Album"),
                "player_name": submitter_name,
                "votes": song.get("votes", 0),
                "voters": song.get("voters", [])
            })
    else:
        converted_songs = songs

    sanitized_rounds = []
    
    for r in results:
        if hasattr(r, "__dict__"):
            round_dict = r.__dict__
        elif hasattr(r, "dict") and callable(getattr(r, "dict")):
            round_dict = r.dict()
        elif isinstance(r, dict):
            round_dict = r
        else:
            continue

        raw_submissions = round_dict.get("submissions", []) or round_dict.get("songs", [])
        flattened_submission_ids = []

        if isinstance(raw_submissions, list):
            for sub in raw_submissions:
                if hasattr(sub, "id"):
                    flattened_submission_ids.append(str(sub.id))
                elif hasattr(sub, "song_id"):
                    flattened_submission_ids.append(str(sub.song_id))
                elif isinstance(sub, dict):
                    sub_id = sub.get("id") or sub.get("song_id") or sub.get("user_id")
                    if sub_id:
                        flattened_submission_ids.append(str(sub_id))
                elif isinstance(sub, (str, int)):
                    flattened_submission_ids.append(str(sub))

        clean_round_item = {
            "round_number": int(round_dict.get("round_number")),
            "title": str(round_dict.get("title", "Unknown Round")),
            "submissions": flattened_submission_ids,
            "description": str(round_dict.get("description", "")),
            "winner": (round_dict.get("winner", []))
        }
        sanitized_rounds.append(clean_round_item)

    results = sorted(sanitized_rounds, key= lambda x: x.get("round_number"))

    players = sorted(players, key=lambda x: x.get("name", "").lower())
    converted_songs = sorted(converted_songs, key=lambda x: x.get("artist", "").lower())

    current_working_data = {
        "players": players,
        "rounds": results,
        "songs": converted_songs
    }
    initialize_memory_cache(current_working_data)

    cache_results = build_static_dashboard_cache(current_working_data)
    processed_players = cache_results.get("players", [])
    precomputed_dashboard_stats = cache_results.get("precomputed_stats", {})
    
    updated_avatars = get_avatar_cache()

    return {
        "rounds": results,
        "songs": converted_songs,
        "players": processed_players,
        "precomputed_stats": precomputed_dashboard_stats,
        "avatars": updated_avatars,
        "username_mapping": config["username-player_name"]
    }

def new_round_check(config): 
    global songs, players, results
    
    from data_collection.web_crawler import get_avatar_cache
    current_avatars = get_avatar_cache()

    if songs and players:
        try:
            updated_results = get_results(config = config, results=results)
            
            if updated_results and updated_results != results:
                results = updated_results
                songs = export_songs(results)
                players = export_players(results, current_avatars)
            elif not updated_results:
                print("Warning: Delta update returned zero results. Retaining existing database cache.")
                
        except Exception as pipeline_err:
            print(f"Gateway pipeline dropped cleanly during sync check: {pipeline_err}")
            print("Falling back to local cached database records to keep the service running.")
        
    elif not songs:
        songs = export_songs(results)
        players = export_players(results, current_avatars)
        print("Initialized missing song/player state matrix data records")
    else:
        players = export_players(results, current_avatars)
        players = export_players(results, current_avatars)