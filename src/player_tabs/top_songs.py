import flet as ft
from data_processing.search_processor import find_song_by_id

def generate_top_songs(player_stats_data):
    """
    Renders an in-memory sub-tab collection illustrating the tracks 
    that received the maximum possible vote scores from the selected user.
    """
    
    top_songs_data = player_stats_data.get("top_songs") or []
    
    
    top_songs_list = ft.Container(
        content=ft.Column(
            controls=[], 
            scroll=ft.ScrollMode.AUTO,
            spacing=15
        ),
        border_radius=10,
        alignment=ft.Alignment.CENTER_LEFT,
        height=600,
        expand=True
    )

    for song_id in top_songs_data:
        song = find_song_by_id(song_id)
        if not song:
            continue
            
        
        song_card = ft.Card(
            content=ft.Container(
                padding=15,
                content=ft.Column(
                    controls=[
                        ft.Row([
                            ft.Icon(ft.Icons.STAR, color="amber", size=24),
                            ft.Text(f"{song.get('name', 'Unknown Track')}", size=22, weight=ft.FontWeight.W_600)
                        ], spacing=10),
                        ft.Text(f"Artist: {song.get('artist', 'Unknown')}", size=16),
                        ft.Text(f"Album: {song.get('album', 'Unknown')}", size=16),
                        ft.Text(f"Submitted By: {song.get('player_name', 'Unknown')}", size=16, color="amber200"),
                        ft.Text(f"Points Received: {song.get('votes', 0)} pts", size=16, weight=ft.FontWeight.BOLD, color="greenAccent200")
                    ],
                    spacing=3
                )
            )
        )
        top_songs_list.content.controls.append(song_card)

    top_songs = ft.Container(
        content=top_songs_list,
        expand=True,
        visible=False
    )

    return top_songs