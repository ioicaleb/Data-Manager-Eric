from data_processing.json_manager import read_json
import re

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
            data.append(song.get("id"))
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
                song_data["songs"].append(song.get("id"))    
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
                data.append(song.get("id"))

    return data

def get_player_avatar(player):
    global players
    
    for player_data in players:
        if player_data.get("name") == player:
            return player_data.get("avatar")

_search_index = None

def init_search_cache():
    """
    Call this function ONCE when your app boots up (e.g., in main() or during data loading).
    It creates an inverted index, mapping single keywords to their respective song dicts.
    """
    global _search_index
    global songs
    _search_index = {}
    
    word_splitter = re.compile(r'[\s\-:,\.\(\)\[\]/\\]+')
    
    for song in songs:
        searchable_text = f"{song.get('name', '')} {song.get('artist', '')} {song.get('album', '')}".lower()
        
        words = set(word_splitter.split(searchable_text))
        
        for word in words:
            if not word:
                continue
            if word not in _search_index:
                _search_index[word] = []
            _search_index[word].append(song)

    print("Search Cache Initialized")

def search_songs(keyword):
    """
    Blazing fast keyword index query using dictionary hashing for instant execution on Render.
    """
    global songs, _search_index
    
    if _search_index is None:
        init_search_cache()
        
    clean_keyword = keyword.strip().lower()
    if not clean_keyword:
        return []
        
    word_splitter = re.compile(r'[\s\-:,\.\(\)\[\]/\\]+')
    query_words = [w for w in word_splitter.split(clean_keyword) if w]
    
    if not query_words:
        return []
        
    # Find all matching songs for each query word
    matched_sets = []
    
    # Track a fast lookup mapping between object memory IDs and the actual song objects
    id_to_song_lookup = {}
    
    for q_word in query_words:
        current_word_songs = []
        
        if q_word in _search_index:
            current_word_songs = _search_index[q_word]
        else:
            # Partial match fallback loop
            partial_matches = []
            for idx_key in _search_index.keys():
                if q_word in idx_key:
                    partial_matches.extend(_search_index[idx_key])
            if partial_matches:
                current_word_songs = partial_matches
            else:
                # No matches found for this word token, return empty list instantly
                return []
                
        word_ids_set = set()
        for song in current_word_songs:
            song_id = id(song)
            id_to_song_lookup[song_id] = song
            word_ids_set.add(song_id)
            
        matched_sets.append(word_ids_set)
                
    # Intersect all hashable ID sets to find songs matching ALL query words cleanly
    if not matched_sets:
        return []
        
    result_ids = matched_sets[0]
    for next_set in matched_sets[1:]:
        result_ids = result_ids.intersection(next_set)
        if not result_ids:
            break
            
    return [id_to_song_lookup[s_id] for s_id in result_ids]

def find_round_by_song_id(song_id):
    global rounds
    for round_item in rounds:
        if song_id in round_item.get("submissions"):
            return round_item

def get_votes_from_data(player_name):
    global songs
    if not songs:
        songs = read_json("songs")

    data = {
        "votes_to_data": {},
        "votes_from_data" : {},
        "votes_songs": {}
    }

    votes_to_data = {}
    votes_from_data = {}
    votes_songs_data = []

    for song in songs:
        if song.get("player_name") != player_name:
            song_submitter = song.get("player_name")
            votes_info = song.get("voters", {})
            for voter in votes_info: 
                voter_name = voter.get("name")
                if voter_name == player_name:
                    votes_songs_data.append(song.get("id"))
                    if song_submitter not in votes_from_data.keys():
                        votes_from_data[song_submitter] = 0
                    votes_from_data[song_submitter] += voter.get("votes")
        else:
            votes_info = song.get("voters", {})
            for voter in votes_info: 
                voter_name = voter.get("name")
                if voter_name != player_name:
                    if voter_name not in votes_to_data.keys():
                        votes_to_data[voter_name] = 0
                    votes_to_data[voter_name] += voter.get("votes")
        
    data["votes_to_data"] = dict(sorted(votes_to_data.items(), key=lambda item: item[1], reverse=True))
    data["votes_from_data"] = dict(sorted(votes_from_data.items(), key=lambda item: item[1], reverse=True))
    data["votes_songs"] = votes_songs_data
    return data