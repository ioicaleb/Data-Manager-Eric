"""
SheetManager.py - Google Sheets integration module for ML WebCrawler

This module handles communication with Google Sheets to:
- Retrieve defunct player information
- Update player sheets with song data
- Generate and post vote matrices
"""

import os.path
from typing import List, Dict, Any, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from DataCollection.Objects import Player_Defunct, Song

# Google Sheets API scope
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Global variables for authentication and configuration
creds: Optional[Credentials] = None
spreadsheet_id: str = ""

def set_spreadsheet_id(config: Dict[str, Any]) -> None:
    """
    Set the spreadsheet ID from configuration
    
    Args:
        config (Dict[str, Any]): Configuration dictionary containing spreadsheet_id
    """
    global spreadsheet_id 
    spreadsheet_id = config.get("spreadsheet_id", "")

def verify_credentials() -> None:
    """
    Verify and refresh Google API credentials
    
    Creates new credentials if they don't exist or are expired
    
    Raises:
        HttpError: If there's an error during credential verification
    """
    global creds

    # Check if token file exists
    if os.path.exists("cache/token.json"):
        creds = Credentials.from_authorized_user_file("cache/token.json", SCOPES)
    
    # Refresh credentials if needed
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Generate new credentials
            flow = InstalledAppFlow.from_client_secrets_file(
                "cache/credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        
        # Save credentials to file
        with open("cache/token.json", "w") as token:
            token.write(creds.to_json())

def parse_players(values: List[List[str]], active_players: List[List[str]]) -> List[Player_Defunct]:
    """
    Parse player data from Google Sheets values
    
    Args:
        values (List[List[str]]): Raw data from Google Sheets
        active_players (List[List[str]]): List of active player names
        
    Returns:
        List[Player_Defunct]: List of defunct player objects with their songs
    """
    # Create set of active player names for efficient lookup
    active_player_names = {ap[1] for ap in active_players}
    
    if not values:
        print("No data found.")
        return []

    players = []
    i = 0
    
    # Process columns (players) in the sheet
    while i < len(values[0]):
        player = Player_Defunct()
        player.songs = []
        j = 0
        
        # Process rows (songs) for this player
        for j, row in enumerate(values):
            # Check for end of data
            if i >= len(row) or not row[i]:
                break
                
            # Skip header rows
            if j == 1:  # Player name row
                player.name = row[i]
                continue
                
            # Skip song title row (j == 2)
            if j == 2:
                continue
            
            # Process song data
            if j > 2 and i < len(row) and row[i]:
                song = Song(row[i])
                player.songs.append(song)
        
        # Only add player if not in active players list
        if player.name not in active_player_names:
            players.append(player)
        
        i += 2  # Move to next player column (assuming 2 columns per player)
    
    return players

def get_defunct_players(config: Dict[str, Any]) -> Optional[List[Player_Defunct]]:
    """
    Retrieve defunct player information from Google Sheets
    
    Args:
        config (Dict[str, Any]): Configuration dictionary
    
    Returns:
        Optional[List[Player_Defunct]]: List of defunct players or None if error
        
    Raises:
        HttpError: If there's an error during data retrieval
    """
    global creds
    global spreadsheet_id

    # Define the range to read from
    range_name = "Votes/Song!A:AD"
    
    verify_credentials()

    try:
        service = build("sheets", "v4", credentials=creds)

        sheet = service.spreadsheets()
        result = (
            sheet.values()
            .get(spreadsheetId=spreadsheet_id, range=range_name)
            .execute()
        )
        values = result.get("values", [])

        if not values:
            print("No data found.")
            return None
            
        return parse_players(values, config.get("username-player_name", []))
        
    except HttpError as err:
        print(f"An error occurred: {err}")
        return None

def post_player_sheet(players: List[Dict[str, Any]], songs: List[Dict[str, Any]]) -> None:
    """
    Update Google Sheets with player information and their songs
    
    Args:
        players (List[Dict[str, Any]]): List of player dictionaries
        songs (List[Dict[str, Any]]): List of song dictionaries
        
    Raises:
        HttpError: If there's an error during data update
    """
    global creds
    global spreadsheet_id

    verify_credentials()

    try:
        service = build("sheets", "v4", credentials=creds)
        data_payloads = []
        
        # Define column ranges for player data (14 columns for 13 players)
        ranges = ["A:B", "C:D", "E:F", "G:H", "I:J", "K:L", "M:N", "O:P", "Q:R", "S:T", "U:V", "W:X", "Y:Z", "AA:AB"]
        
        # Process each player
        for j, player in enumerate(players):
            # Limit to available column ranges
            if j >= len(ranges):
                print(f"Warning: Ran out of column ranges for player {player['name']}")
                break
            
            # Prepare player data
            values = [[player["name"]], ["Song", "Votes"]]
            player_songs = [song for song in songs if song['player_name'] == player["name"]]
            
            # Sort songs by votes (descending) then by name
            player_songs = sorted(player_songs, key=lambda x: (-x["votes"], x["name"]))
            
            # Add songs to player data
            for song in player_songs:
                values.append([song["name"], song["votes"]])
                
            # Add data to payload
            data_payloads.append({
                "range": f"Votes/Song!{ranges[j]}",
                "values": values
            })
        
        # Batch update sheets
        if data_payloads:
            body = {
                "valueInputOption": "RAW",
                "data": data_payloads
            }
            
            service.spreadsheets().values().batchUpdate(
                spreadsheetId=spreadsheet_id, 
                body=body
            ).execute()
            
            print("Players sheet successfully updated.")
        else:
            print("No data to update in players sheet.")

    except HttpError as err:
        print(f"An error occurred: {err}")

def post_vote_matrix(vm_rounds: List[Dict[str, Any]]) -> None:
    """
    Generate and post vote matrices to Google Sheets
    
    Args:
        vm_rounds (List[Dict[str, Any]]): List of vote matrix rounds
        
    Raises:
        HttpError: If there's an error during data update
    """
    print("Preparing data to be written as vote matrix")
    global creds
    global spreadsheet_id

    verify_credentials()

    try:
        service = build("sheets", "v4", credentials=creds)
        matrices = []
        round_ranges = []
        values = []
        
        # Create round range labels
        for i in range(1, len(vm_rounds) + 10, 10):
            round_ranges.append(f"{i}-{i + 9}")
        
        # Process each round
        for round_data in vm_rounds:
            voters = round_data["voters"]
            matrix = [[""], ]  # Start with empty first row
            
            # Add player names as column headers
            for player in round_data["players"]:
                matrix[0].append(player)
            
            # Add voter data
            for voter in voters:
                row = [voter["name"]]
                for player in voter["votes"]:
                    row.append(player["votes"])
                matrix.append(row)    
            
            # Add empty row at end
            matrix.append([""])
            matrices.append(matrix)
            
            # Batch update when we have 10 matrices or it's the last round
            if len(matrices) == 10 or int(round_data["id"]) == len(vm_rounds):
                # Determine the batch index
                if len(matrices) == 10:
                    range_index = int((int(round_data["id"]) / 10) - 1)
                else: 
                    range_index = int((int(round_data["id"]) / 10))
                
                # Flatten matrices into single data array
                data = []
                for matrix in matrices:
                    data.extend(matrix)
                
                # Add to values payload
                values.append({
                    "range": f"Vote Matrix {round_ranges[range_index]}!B2:R",
                    "values": data
                })
                
                # Execute batch update
                body = {
                    "valueInputOption": "RAW",
                    "data": values
                }
                
                service.spreadsheets().values().batchUpdate(
                    spreadsheetId=spreadsheet_id, 
                    body=body
                ).execute()
                
                # Reset for next batch
                values = []
                matrices = []
        
        print("Vote matrix successfully updated.")

    except HttpError as err:
        print(f"An error occurred: {err}")

def post_master_matrix(matrix_data):
    print("Preparing data to be written as vote matrix")
    global creds
    global spreadsheet_id

    verify_credentials()

    try:
        service = build("sheets", "v4", credentials=creds)
        values = []        
        matrix = []  # Start with empty first row
        
        # Add voter data
        for voter in matrix_data:
            row = []
            if isinstance(voter, list):
                # Add player names as column headers
                matrix.append(matrix_data[0])
            else:
                row = [voter["name"]]
                for player in voter["votes"]:
                    row.append(player["votes"])
                matrix.append(row)

        
        # Add to values payload
        values.append({
            "range": f"Vote Matrix!B2:Q",
            "values": matrix
        })
        
        # Execute batch update
        body = {
            "valueInputOption": "RAW",
            "data": values
        }
        
        service.spreadsheets().values().batchUpdate(
            spreadsheetId=spreadsheet_id, 
            body=body
        ).execute()
        
        print("Vote matrix successfully updated.")

    except HttpError as err:
        print(f"An error occurred: {err}")