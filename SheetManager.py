import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from Objects import Player_Defunct, Song

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

creds = None

def verify_credentials():
  global creds

  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists("cache/token.json"):
    creds = Credentials.from_authorized_user_file("cache/token.json", SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "cache/credentials.json", SCOPES
      )
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("cache/token.json", "w") as token:
      token.write(creds.to_json())

#Converts sheets information to a player and adds them to defunct players list if they are not in the active group
def parse_players(values, active_players):
    players = []
    ap_names = []
    for ap in active_players:
        ap_names.append(ap[1])

    if not values:
        print("No data found.")
        return

    i = 0
    while i < len(values[0]):
      player = Player_Defunct()
      player.songs = []
      j = 0
      for row in values:
        j += 1
        if i >= len(row) or not row[i]:
            break
        if j == 1:
            player.name = row[i]
            continue
        if (i + 1) >= len(row) or not row[i + 1]:
            break
        if j == 2:
            continue
        
        song = Song(row[i])
        player.songs.append(song)
      if player.name not in ap_names:
        players.append(player)
      i += 2
    return players

#Finds player names for players that have left the league
def get_defunct_players(config):
  global creds

  spreadsheetId = config.get("spreadsheet_id")
  range = "Votes/Song!A:AD"
  
  verify_credentials()

  try:
    service = build("sheets", "v4", credentials=creds)

    # Call the Sheets API
    sheet = service.spreadsheets()
    result = (
        sheet.values()
        .get(spreadsheetId=spreadsheetId, range=range)
        .execute()
    )
    values = result.get("values", [])

    if not values:
      print("No data found.")
      return
    return parse_players(values, config.get("username-player_name"))
  except HttpError as err:
    print(err)

def post_player_sheet(config, players, songs):
  global creds

  verify_credentials()

  try:
    service = build("sheets", "v4", credentials=creds)
    # Call the Sheets API
    data_payloads = []
    ranges = ["A:B", "C:D", "E:F", "G:H", "I:J", "K:L", "M:N", "O:P", "Q:R", "S:T", "U:V", "W:X", "Y:Z", "AA:AB", "AC:AD"]
    for j, player in enumerate(players):
      if j >= len(ranges):
          print(f"Warning: Ran out of column ranges for player {player['name']}")
          break
          
      values = [[player["name"]], ["Song", "Votes"]]
      player_songs = [song for song in songs if song['player_name'] == player["name"]]
      player_songs = sorted(player_songs, key = lambda x: (-x["votes"], x["name"]))
      for song in player_songs:
          values.append([song["name"], song["votes"]])
          
      data_payloads.append({
          "range": f"Votes/Song!{ranges[j]}",
          "values": values
      })
      
      body = {
          "valueInputOption": "RAW",
          "data": data_payloads
      }
      
      result = (
          service.spreadsheets()
          .values()
          .batchUpdate(
              spreadsheetId=config.get("spreadsheet_id"),
              body=body
          )
          .execute()
      )
    print("Players sheet successfully updated.")

  except HttpError as err:
    print(err)

def post_vote_matrix(config, rounds, songs):
   return 
  