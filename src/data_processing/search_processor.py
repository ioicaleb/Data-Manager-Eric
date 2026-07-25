from data_processing.cache_manager import read_json
import re

songs = None
players = None
rounds = None
_search_index = None

def clear_search_processor_globals():
    """
    Crucial for a shared cloud server! Clear memory states when changing 
    leagues so players never see cached leaks from other sessions.
    """
    global songs, players, rounds, _search_index
    songs = None
    players = None
    rounds = None
    _search_index = None
    print("Search processor globals completely cleared for a fresh session sync.")

def get_songs():
    global songs
    if songs is None:
        songs = read_json("songs") or []
    return songs

def get_rounds():
    global rounds
    if rounds is None:
        rounds = read_json("rounds") or []
    return rounds

def get_players():
    global players
    if players is None:
        players_list = read_json("players") or []
        
        sorted_players = sorted(players_list, key=lambda x: x.get("votes_to", 0), reverse=True)

        for player in players_list:        
            index = next((index for index, p in enumerate(sorted_players) if p.get("name") == player.get("name")), None)
            player["position"] = f"#{index + 1}" if index is not None else "#?"
        players = players_list
    return players

def find_songs_by_title(title):
    data = []
    all_songs = get_songs()
    for song in all_songs:
        if title.lower() in song.get("name", "").lower():
            data.append(song)
    return data

def find_song_by_id(id):
    all_songs = get_songs()
    for song in all_songs:
        if song.get("id") == id:
            return song
    print(f"Can't find song with id {id}")
    return None

def find_songs_by_artist(artist):
    data = []
    all_songs = get_songs()
    for song in all_songs:
        if artist.lower() in song.get("artist", "").lower():
            data.append(song)
    return data

def find_songs_by_album(album):
    data = []
    all_songs = get_songs()
    for song in all_songs:
        if album.lower() in song.get("album", "").lower():
            data.append(song)
    return data

def find_songs_by_submitter(submitter):
    data = []
    all_songs = get_songs()
    for song in all_songs:
        if submitter.lower() == song.get("player_name", "").lower():
            data.append(song.get("id"))
    return data

def find_player_songs_by_round(player_name):
    data = []
    all_rounds = get_rounds()
    all_songs = get_songs()
    for round_obj in all_rounds:
        song_data = {
            "round_id": round_obj.get("id"),
            "title": round_obj.get("title"),
            "songs": []
        }
        for song in all_songs:
            if song.get("id") in round_obj.get("submissions", []) and song.get("player_name", "").lower() == player_name.lower():
                song_data["songs"].append(song.get("id"))    
        if song_data["songs"]:
            data.append(song_data)
    data = sorted(data, key=lambda x: x.get("round_id", 0))
    return data

def find_songs_by_voter(voter_name):
    data = []
    all_songs = get_songs()
    for song in all_songs:
        voters = song.get("voters", [])
        for voter in voters:
            if voter.get("name", "").lower() == voter_name.lower():
                data.append(song)

    data = sorted(data, key=lambda x: x.get("artist", "").lower())
    return data

def find_top_songs(voter_name):
    data = []
    matched_songs = find_songs_by_voter(voter_name)
    for song in matched_songs:
        voters = song.get("voters", [])
        for voter in voters:
            if voter.get("name", "").lower() == voter_name.lower() and int(voter.get("votes", 0)) == 4:
                data.append(song.get("id"))
    return data

def get_player_avatar(player):
    all_players = get_players()
    for player_data in all_players:
        if player_data.get("name") == player:
            return player_data.get("avatar")
    return None

def init_search_cache():
    """
    Creates an inverted index, mapping single keywords to their respective song dicts.
    FIXED: Calls get_songs() to guarantee data hydration before caching.
    """
    global _search_index
    _search_index = {}
    
    all_songs = get_songs()
    
    word_splitter = re.compile(r'[\s\-:,\.\(\)\[\]/\\]+')
    
    for song in all_songs:
        searchable_text = f"{song.get('name', '')} {song.get('artist', '')} {song.get('album', '')}".lower()
        words = set(word_splitter.split(searchable_text))
        
        for word in words:
            if not word:
                continue
            if word not in _search_index:
                _search_index[word] = []
            _search_index[word].append(song)

    print("Inverted Search Index Successfully Generated.")

def search_songs(keyword):
    """
    Blazing fast keyword index query using dictionary hashing for instant execution on Render.
    """
    global _search_index
    
    if _search_index is None:
        init_search_cache()
        
    clean_keyword = keyword.strip().lower()
    if not clean_keyword:
        return []
        
    word_splitter = re.compile(r'[\s\-:,\.\(\)\[\]/\\]+')
    query_words = [w for w in word_splitter.split(clean_keyword) if w]
    
    if not query_words:
        return []
        
    matched_sets = []
    id_to_song_lookup = {}
    
    for q_word in query_words:
        current_word_songs = []
        
        if q_word in _search_index:
            current_word_songs = _search_index[q_word]
        partial_matches = []
        for idx_key in _search_index.keys():
            if q_word in idx_key:
                partial_matches.extend(_search_index[idx_key])
        if partial_matches:
            current_word_songs = partial_matches
        else:
            return []
                
        word_ids_set = set()
        for song in current_word_songs:
            song_id = id(song)
            id_to_song_lookup[song_id] = song
            word_ids_set.add(song_id)
            
        matched_sets.append(word_ids_set)
                
    if not matched_sets:
        return []
        
    result_ids = matched_sets[0]
    for next_set in matched_sets[1:]:
        result_ids = result_ids.intersection(next_set)
        if not result_ids:
            break
            
    return [id_to_song_lookup[s_id] for s_id in result_ids]

def find_round_by_song_id(song_id):
    all_rounds = get_rounds()
    for round_item in all_rounds:
        if song_id in round_item.get("submissions", []):
            return round_item
    return None

def get_votes_from_data(player_name):
    all_songs = get_songs()

    data = {
        "votes_to_data": {},
        "votes_from_data" : {},
        "votes_songs": []
    }

    votes_to_data = {}
    votes_from_data = {}
    votes_songs_data = []

    sorted_songs = sorted(all_songs, key=lambda x: x.get("artist", "").lower())

    for song in sorted_songs:
        s_submitter = song.get("player_name", "Unknown")
        votes_info = song.get("voters", [])
        
        if s_submitter.lower() != player_name.lower():
            for voter in votes_info: 
                voter_name = voter.get("name", "")
                if voter_name.lower() == player_name.lower():
                    votes_songs_data.append(song.get("id"))
                    if s_submitter not in votes_from_data:
                        votes_from_data[s_submitter] = 0
                    votes_from_data[s_submitter] += int(voter.get("votes", 0))
        else:
            for voter in votes_info: 
                voter_name = voter.get("name", "")
                if voter_name.lower() != player_name.lower():
                    if voter_name not in votes_to_data:
                        votes_to_data[voter_name] = 0
                    votes_to_data[voter_name] += int(voter.get("votes", 0))
        
    data["votes_to_data"] = dict(sorted(votes_to_data.items(), key=lambda item: item[1], reverse=True))
    data["votes_from_data"] = dict(sorted(votes_from_data.items(), key=lambda item: item[1], reverse=True))
    data["votes_songs"] = votes_songs_data
    return data