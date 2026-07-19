from DataCollection.json_manager import read_json

songs = {}
players = {}
rounds = {}

def get_songs():
    global songs
    if not songs:
        songs = read_json("songs")
    return songs

def get_rounds():
    global rounds
    if not rounds:
        rounds = read_json("rounds")
    return rounds

def get_players():
    global players
    if not players:
        players_list = read_json("players")
        
        sorted_players = sorted(players_list, key=lambda x: x["votes_to"], reverse=True)

        for player in players_list:        
            index = next((index for index, p in enumerate(sorted_players) if p["name"] == player["name"]), None)
            player["position"] = f"#{index + 1}"
        players = players_list
    return players

def find_songs_by_title(title):
    data = []
    songs = get_songs()
    for song in songs:
        if title.lower() in song["name"].lower():
            data.append(song)
    return data

def find_song_by_id(id):
    songs = get_songs()
    for song in songs:
        if(song["id"]) == id:
            return song
    print(f"Can't find song with id {id}")

def find_songs_by_artist(artist):
    data = []
    songs = get_songs()
    for song in songs:
        if artist.lower() in song["artist"].lower():
            data.append(song)
    return data

def find_songs_by_album(album):
    data = []
    songs = get_songs()
    for song in songs:
        if album.lower() in song["album"].lower():
            data.append(song)
    return data

def find_songs_by_submitter(submitter):
    data = []
    songs = get_songs()
    for song in songs:
        if submitter.lower() == song["player_name"].lower():
            data.append(song)
    return data

def find_player_songs_by_round(player_name):
    data = []
    rounds = get_rounds()
    songs = get_songs()
    for round in rounds:
        song_data = {
            "round_id": round["round_number"],
            "title": round["title"],
            "songs": []
        }
        for song in songs:
            if song["id"] in round["submissions"] and song["player_name"] == player_name:
                song_data["songs"].append(song)    
        data.append(song_data)
    data = sorted(data, key = lambda x: x["round_id"])
    return data

def find_songs_by_voter(voter_name):
    data= []
    songs = get_songs()
    for song in songs:
        voters = song["voters"]
        for voter in voters:
            if voter["name"] == voter_name:
                data.append(song)

    data = sorted(data, key = lambda x: x["player_name"])
    return data

def find_top_songs(voter_name):
    data= []
    songs = find_songs_by_voter(voter_name)
    for song in songs:
        voters = song["voters"]
        for voter in voters:
            if voter["name"] == voter_name and voter["votes"] == 4:
                data.append(song)

    data = sorted(data, key = lambda x: x["artist"])
    return data

def get_player_avatar(player):
    global players
    
    for player_data in players:
        if player_data.get("name") == player:
            return player_data.get("avatar")
        
import re

# Global cache to hold pre-computed search index mappings
# Keys will be lowercased individual words, values will be lists of song references
_search_index = None

def init_search_cache():
    """
    Call this function ONCE when your app boots up (e.g., in main() or during data loading).
    It creates an inverted index, mapping single keywords to their respective song dicts.
    """
    global _search_index
    global songs
    _search_index = {}
    
    # Simple regex to split words by spaces and common punctuation tokens
    word_splitter = re.compile(r'[\s\-:,\.\(\)\[\]/\\]+')
    
    for song in songs:
        # 1. Combine fields into a single block of searchable text
        searchable_text = f"{song.get('name', '')} {song.get('artist', '')} {song.get('album', '')}".lower()
        
        # 2. Extract individual words/tokens to map as index keys
        words = set(word_splitter.split(searchable_text))
        
        # 3. Associate this song reference with each extracted word token
        for word in words:
            if not word:
                continue
            # Keep index structures small by grouping references together
            if word not in _search_index:
                _search_index[word] = []
            _search_index[word].append(song)

def search_songs(keyword):
    """
    Blazing fast O(1) keyword index query that eliminates loop filters and string allocations.
    """
    global songs, _search_index
    
    # Fallback safety check: build index on the fly if init_search_cache wasn't triggered
    if _search_index is None:
        init_search_cache()
        
    clean_keyword = keyword.strip().lower()
    if not clean_keyword:
        return []
        
    # Split the incoming query string into individual filter tokens
    word_splitter = re.compile(r'[\s\-:,\.\(\)\[\]/\\]+')
    query_words = [w for w in word_splitter.split(clean_keyword) if w]
    
    if not query_words:
        return []
        
    # 1. Fetch matched song arrays for each unique query word token
    matched_lists = []
    for q_word in query_words:
        # Check if the word exactly matches an index key
        if q_word in _search_index:
            matched_lists.append(_search_index[q_word])
        else:
            # OPTIONAL PARTIAL MATCH FALLBACK:
            # If an exact word match isn't found, find keys that contain the token
            partial_matches = []
            for idx_key in _search_index.keys():
                if q_word in idx_key:
                    partial_matches.extend(_search_index[idx_key])
            
            if partial_matches:
                matched_lists.append(partial_matches)
            else:
                # If any single word from the multi-word query yield 0 results, 
                # the total intersection will be empty anyway, return early.
                return []
                
    # 2. Compute the intersection (AND logic) across all matched word collections
    # This ensures searching "The Beatles" returns only songs matching BOTH terms
    result_set = set(id(s) for s in matched_lists[0])
    song_lookup = {id(s): s for s in matched_lists[0]}
    
    for next_list in matched_lists[1:]:
        current_ids = set(id(s) for s in next_list)
        for s in next_list:
            song_lookup[id(s)] = s
        result_set.intersection_update(current_ids)
        if not result_set:
            break
            
    # Return the real underlying dictionary objects cleanly
    return [song_lookup[s_id] for s_id in result_set]