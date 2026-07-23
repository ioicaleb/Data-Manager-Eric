import flet as ft
from data_processing.search_processor import find_song_by_id

def generate_top_songs(player_stats_data):
    top_songs_data = player_stats_data.get("top_songs") or {}
    top_songs_list = ft.Container(
        content = ft.Column(
            controls = [], 
            scroll= ft.ScrollMode.HIDDEN,
        ),
        border_radius=10,
        alignment=ft.Alignment.CENTER_LEFT
    )

    for song_id in top_songs_data:
        song = find_song_by_id(song_id)
        song_details = (f"{song.get('name')}\n"
                        f"Artist: {song.get('artist')}\n"
                        f"Album: {song.get('album')}\n"
                        f"Submitted By: {song.get('player_name')}")
        top_songs_list.content.controls.append(ft.Text(song_details, size=20))

    top_songs = ft.Container(
        content= top_songs_list,
        expand=True,
        visible=False
    )

    return top_songs