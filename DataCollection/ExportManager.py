"""
ExportManager.py - Data export module for ML WebCrawler

This module handles exporting data from the ML WebCrawler to JSON files:
- Exporting player information
- Exporting song information
- Exporting round information
"""

from DataCollection.Objects import Player
from DataCollection.JSONManager import *

# Global variable to cache songs data
songs = []

def get_song(song_id: str) -> dict:
    """
    Retrieve a song by its ID from the cached songs list
    
    Args:
        song_id (str): The unique identifier for the song
        
    Returns:
        dict: The song data dictionary
        
    Raises:
        IndexError: If no song with the given ID is found
    """
    global songs
    
    # Load songs data if not already loaded
    if not songs:
        songs = read_json("songs")
    
    # Find and return the song with matching ID
    try:
        song = [song for song in songs if song['id'] == song_id][0]
        if song:
            return song
    except IndexError:
        print(f"Could not find song with id {song_id}")
        raise

def export_players(rounds: list) -> list:
    """
    Export player data from rounds to JSON file
    
    Args:
        rounds (list): List of round objects containing submissions and winners
        
    Returns:
        list: Sorted list of player dictionaries
    """
    players = []
    
    # Process each round
    for round_obj in rounds:
        # Convert to dict if it's an object
        if not isinstance(round_obj, dict):
            round_obj = round_obj.__dict__
        
        # Process each submission in the round
        for song in round_obj["submissions"]:
            # Get song data
            if isinstance(song, str):
                song = get_song(song)
            if not isinstance(song, dict):
                song = song.__dict__
            
            # Create player object
            player = Player(name=song["player_name"], votes_to=0)
            
            # Check if player already exists
            existing_player = next((p for p in players if player.name == p["name"]), None)
            
            # Add new player or update existing one
            if not existing_player:
                player.wins = 0
                players.append(player.__dict__)
            else:
                # Update existing player's votes
                existing_player["votes_to"] += song["votes"]
        
        # Process winners for each round
        for name in round_obj["winner"]:
            winner = next((p for p in players if p["name"] == name), None)
            if winner:
                winner["wins"] += 1
    
    # Sort players by name
    players = sorted(players, key=lambda x: x["name"])
    
    # Write to JSON file
    write_json("players", players)
    return players

def export_songs(rounds: list) -> list:
    """
    Export song data from rounds to JSON file
    
    Args:
        rounds (list): List of round objects containing submissions
        
    Returns:
        list: Sorted list of song dictionaries
    """
    all_songs = []
    
    # Process each round
    for round_obj in rounds:
        song_number = 1
        
        # Convert to dict if it's an object
        if not isinstance(round_obj, dict):
            round_obj = round_obj.__dict__
        
        # Process each submission in the round
        for song in round_obj["submissions"]:
            # Get song data
            if isinstance(song, str):
                song = get_song(song)
            if not isinstance(song, dict):
                song = song.__dict__
            
            # Convert voters to dict if needed
            if not isinstance(song["voters"][0], dict):    
                song["voters"] = [vars(voter) for voter in song["voters"]]
            
            # Generate unique ID for song
            song["id"] = f"{song['player_name'][:3].lower()}{song_number:02d}{round_obj['round_number']:02d}"
            all_songs.append(song)
            song_number += 1
    
    # Sort songs by player name and votes (descending)
    songs = sorted(all_songs, key=lambda x: (x["player_name"], -x["votes"]))
    
    # Write to JSON file
    write_json("songs", songs)
    return songs

def export_rounds(rounds: list) -> list:
    """
    Export round data from rounds to JSON file
    
    Args:
        rounds (list): List of round objects to export
        
    Returns:
        list: List of round dictionaries
    """
    # Export songs and players first
    export_songs(rounds)
    export_players(rounds)
    
    results = []
    
    # Process each round
    for round_obj in rounds:
        # Convert to dict if it's an object
        if not isinstance(round_obj, dict):
            round_obj = round_obj.__dict__
        
        songs_list = []
        song_number = 1
        
        # Process each submission in the round
        for song in round_obj["submissions"]:
            # Generate unique ID for song
            if not isinstance(song, str):
                song.id = f"{song.player_name[:3].lower()}{song_number:02d}{round_obj['round_number']:02d}"
                songs_list.append(song.id)
            else:
                songs_list.append(song)
            song_number += 1
        
        # Update submissions in round
        if songs_list:
            round_obj["submissions"] = songs_list
        
        # Add round to results
        results.append(round_obj)
    
    # Write to JSON file
    write_json("rounds", results)   
    return results