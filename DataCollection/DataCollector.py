"""
Hawkeyes.py - Main execution module for ML WebCrawler

This module serves as the entry point for the web crawler application,
handling the main workflow of fetching data, processing results,
and exporting to spreadsheet.

Functions:
    main() - Main execution function that orchestrates the crawling process
"""

from DataCollection.WebCrawler import get_results, check_for_new_rounds
from DataCollection.ExportManager import export_players, export_songs
from DataCollection.SheetManager import set_spreadsheet_id, post_player_sheet, post_vote_matrix, post_master_matrix
from DataCollection.JSONManager import read_json
from DataCollection.StatManager import vote_matrix_analysis, master_voter_matrix
import sys

def collect_data():
    """
    Main execution function that orchestrates the crawling process.
    
    This function:
    1. Reads configuration
    2. Sets up spreadsheet ID
    3. Checks for existing results
    4. Handles new rounds detection
    5. Processes results and exports to spreadsheet
    6. Performs statistical analysis
    """
    # Read configuration from JSON
    config = read_json("config")
    
    # Set up the spreadsheet ID for Google Sheets operations
    set_spreadsheet_id(config)
    
    # Attempt to read existing results from JSON
    results = read_json("rounds")
    
    if results:
        print("Pulled previous results")
        
        # Try to read cached songs and players
        songs = read_json("songs")
        players = read_json("players")
        
        # Check if we have both songs and players cached
        if songs and players:
            # Get the last round number from existing results
            last_round_number = results[-1]["round_number"]
            
            # Check if there are new rounds available
            if check_for_new_rounds(last_round_number, config):
                # Re-read songs and players (in case they were updated)
                songs = read_json("songs")
                players = read_json("players")
                
                # Post player sheet to Google Sheets
                post_player_sheet(players, songs)
                print("Stat sheet updated successfully")
        
        # Handle case where cache is missing
        elif not songs:
            # Export songs and players to create cache
            export_songs(results)
            export_players(results)
            print("Failed to get songs cache")
        else:
            # Export players only
            export_players(results)
            print("Failed to get players cache")
    
    else:
        # No existing results, fetch new ones
        results = get_results(config)
    
    # Process results if they were successfully obtained
    if results:
        print("Results successfully obtained")
        
        # Perform statistical analysis on vote matrix
        vm_results = vote_matrix_analysis(results)
        
        # If analysis was successful, post to spreadsheet
        if vm_results:
            post_vote_matrix(vm_results)
            post_master_matrix(master_voter_matrix(vm_results))
    else:
        # If crawling failed, exit with error
        print("Crawl failed")