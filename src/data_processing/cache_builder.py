from data_processing.json_manager import read_json, write_json
from data_processing.data_processor import *
import os,requests, io
from PIL import Image

def download_avatar_locally(url, player_name):
    """Downloads an external avatar image and saves it locally in assets."""
    if not url:
        return None
        
    base_dir = os.path.dirname(os.path.abspath(__file__))
    avatar_dir = os.path.join(base_dir, "assets/avatars")
    os.makedirs(avatar_dir, exist_ok=True)
    
    output_path = os.path.join(avatar_dir, f"{player_name}.png")
    
    if os.path.exists(output_path):
        return f"/avatars/{player_name}.png"
        
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            img = Image.open(io.BytesIO(response.content))
            
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
                
            img.thumbnail((150, 150), Image.Resampling.LANCZOS)
            
            img.save(output_path, "JPEG", quality=80) 

            return f"/avatars/{player_name}.png"
    except Exception as e:
        print(f"Could not optimize asset for {player_name}: {e}")

def build_static_dashboard_cache():
    print("Starting local stats pre-computation...")
    
    players = read_json("players") or []
    
    for player in players:
        cached_dashboard = {}
        player_name = player.get("name")
        top_songs_data = find_top_songs(player_name) or []
        all_songs_data = find_songs_by_submitter(player_name) or []
        round_songs_data = find_player_songs_by_round(player_name) or {}
        votes_data = get_votes_from_data(player_name) or {}
        if not player_name:
            continue

        remote_url = player.get("avatar")
        local_web_path = download_avatar_locally(remote_url, player_name)
        
        player_stats_data = process_player_stats(
            player, 
            top_songs_data, 
            all_songs_data,
            round_songs_data, 
            votes_data
        )
        player["num_comments"] = player_stats_data.get("comments")
        
        player_stats_data["top_songs"] = top_songs_data or []
        player_stats_data["all_songs"] = all_songs_data or []
        player_stats_data["rounds_songs"] = round_songs_data or {}
        player_stats_data["avatar_url"] = local_web_path
        cached_dashboard[player_name] = player_stats_data
        
        write_json(data = cached_dashboard, filename=f"precomputed_stats_{player_name}")

    write_json(data = players, filename="players")
    print(f"Success! Generated master cache")

if __name__ == "__main__":
    build_static_dashboard_cache()