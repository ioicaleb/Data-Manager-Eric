import flet as ft
from data_processing.search_processor import find_song_by_id

def generate_round_songs(player_stats_data):
    round_songs_data = player_stats_data.get("rounds_songs") or {}

    round_songs_list = ft.Container(
        content=ft.Column(
            controls=[], 
            scroll=ft.ScrollMode.HIDDEN,
            spacing=20
        ),
        border_radius=10,
        height=600,
    )

    for round_item in round_songs_data:
        if round_item.get("songs"):
            round_block = ft.Column(
                controls=[
                    ft.Text(
                        f"Round {round_item.get('round_id')} - {round_item.get('title')}:", 
                        size=22, 
                        weight=ft.FontWeight.BOLD
                    ),
                ],
                spacing=10
            )
            song_details = ft.Container(
                content=ft.Column(controls=[], spacing=10)
            )

            for song_id in round_item["songs"]:
                song = find_song_by_id(song_id)
                song_info = ft.Column(
                    controls=[
                        ft.Text(f"{song.get('name')}", size=20, weight=ft.FontWeight.W_500),
                        ft.Text(f"Artist: {song.get('artist')}", size=18),
                        ft.Text(f"Album: {song.get('album')}", size=18),
                        ft.Text(f"Votes: {song.get('votes')}", size=18),
                    ],
                    spacing = 2,
                    margin = ft.Margin(40, 0, 0, 0)
                )
                song_details.content.controls.append(song_info)
            
            round_block.controls.append(song_details)
            round_songs_list.content.controls.append(round_block)
            round_songs_list.content.controls.append(
                ft.Divider(height=10, thickness=1, color=ft.Colors.GREY_800)
            )

    round_songs = ft.Container(
        content= round_songs_list,
        expand=True,
        visible=False
    )

    return round_songs