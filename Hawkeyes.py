from WebCrawler import get_results, check_for_new_rounds
from ExportManager import export_players, export_songs
from SheetManager import post_player_sheet
from JSONManager import read_json
import sys

# TODO: VOTE MATRIX
# TODO: Statistical analysis

def main():
    config = read_json("config")
    results = read_json("rounds")
    if results:
        print("Pulled previous results")
        songs = read_json("songs")
        players = read_json("players")
        if songs and players:
            last_round_number = results[-1]["round_number"]
            if check_for_new_rounds(last_round_number, config):
                songs = read_json("songs")
                players = read_json("players")
                post_player_sheet(config, players, songs)
                print("Stat sheet updated successfully")
        elif not songs:
            export_songs(results)
            export_players(results)
            print("Failed to get songs cache")
        else:
            export_players(results)
            print("Failed to get players cache")
    else:
        results = get_results(config)
        if results:
            print("Results successfully obtained")
        else:
            print("Crawl failed")
            sys.exit()

if __name__ == "__main__":
    main()