import flet as ft
from data_processing.search_processor import find_song_by_id

def generate_all_songs(player_stats_data):
    all_songs_data = player_stats_data.get("all_songs") or {}

    all_songs_list =  ft.Container(
                content = ft.Column(
                    controls = [], 
                    scroll= ft.ScrollMode.HIDDEN,
                ),
                border_radius=10,
                height= 600,
                alignment=ft.Alignment.CENTER_LEFT
            )
            
    for song_id in all_songs_data:
        song = find_song_by_id(song_id)
        song_details = (f"{song.get('name')}\n"
                        f"Artist: {song.get('artist')}\n"
                        f"Album: {song.get('album')}\n"
                        f"Votes: {song.get('votes')}")
        all_songs_list.content.controls.append(ft.Text(song_details, size=20))
    
    all_songs = ft.Container(
        content= all_songs_list,
        expand=True,
        visible=False
    )

    return all_songs