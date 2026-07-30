import flet as ft
from data_processing.search_processor import find_song_by_id

def generate_all_songs(player_stats_data):
    """
    Renders an in-memory sub-tab ledger showcasing every single track
    submitted by the selected user across all rounds of the music league.
    """
    all_songs_data = player_stats_data.get("all_songs") or []

    all_songs_list = ft.Container(
        content=ft.Column(
            controls=[], 
            scroll=ft.ScrollMode.HIDDEN,
            spacing=15
        ),
        border_radius=10,
        height=600,
        alignment=ft.Alignment.CENTER_LEFT,
        expand=True
    )
            
    for song_id in all_songs_data:
        song = find_song_by_id(song_id)
        if not song:
            continue
            
        song_card = ft.Card(
            content=ft.Container(
                padding=15,
                content=ft.Column(
                    controls=[
                        ft.Row([
                            ft.Icon(ft.Icons.MUSIC_NOTE, color="purple200", size=24),
                            ft.Text(f"{song.get('name', 'Unknown Track')}", size=22, weight=ft.FontWeight.W_600)
                        ], spacing=10),
                        ft.Text(f"Artist: {song.get('artist', 'Unknown')}", size=16),
                        ft.Text(f"Album: {song.get('album', 'Unknown')}", size=16),
                        ft.Text(f"Total Votes Accumulated: {song.get('votes', 0)} pts", size=16, weight=ft.FontWeight.BOLD, color="greenAccent200")
                    ],
                    spacing=3
                )
            )
        )
        all_songs_list.content.controls.append(song_card)
    
    all_songs = ft.Container(
        content=all_songs_list,
        expand=True,
        visible=False
    )

    return all_songs