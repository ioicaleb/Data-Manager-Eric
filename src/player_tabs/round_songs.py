import flet as ft
from data_processing.search_processor import find_song_by_id

def generate_round_songs(player_stats_data):
    """
    Renders an in-memory sub-tab ledger displaying the tracks 
    submitted by the selected user, organized chronologically by round.
    """
    round_songs_data = player_stats_data.get("rounds_songs") or {}

    
    round_songs_list = ft.Container(
        content=ft.Column(
            controls=[], 
            scroll=ft.ScrollMode.HIDDEN,
            spacing=25
        ),
        border_radius=10,
        expand=True,
    )

    
    if isinstance(round_songs_data, dict):
        iterations = round_songs_data.values()
    else:
        iterations = round_songs_data if round_songs_data else []

    for round_item in iterations:
        if isinstance(round_item, dict) and round_item.get("songs"):
            round_block = ft.Column(
                controls=[
                    ft.Text(
                        f"Round {round_item.get('round_number', '?')} — {round_item.get('title', 'Unknown Round Title')}:", 
                        size=22, 
                        weight=ft.FontWeight.BOLD,
                        color="purple100"
                    ),
                ],
                spacing=10
            )
            song_details = ft.Container(
                content=ft.Column(controls=[], spacing=10)
            )

            for song_id in round_item["songs"]:
                song = find_song_by_id(song_id)
                if not song:
                    continue
                    
                
                song_info = ft.Column(
                    controls=[
                        ft.Text(f"🎵 {song.get('name', 'Unknown Track')}", size=24, weight=ft.FontWeight.W_500, color="amber100"),
                        ft.Text(f"Artist: {song.get('artist', 'Unknown')}", size=18),
                        ft.Text(f"Album: {song.get('album', 'Unknown')}", size=18),
                        ft.Text(f"Comment: {song.get('user_comment', '')}", size=18) if song.get('user_comment') else None,
                        ft.Text(f"Round Points Accumulated: {song.get('votes', 0)} pts", size=18, weight=ft.FontWeight.BOLD)
                    ],
                    spacing=3,
                    margin=ft.Margin(left=40)
                )

                song_info.controls = [c for c in song_info.controls if c is not None]
                
                song_details.content.controls.append(
                    ft.Card(content=ft.Container(content=song_info, padding=12), expand = True)
                )
            
            round_block.controls.append(song_details)
            round_songs_list.content.controls.append(round_block)
            round_songs_list.content.controls.append(
                ft.Divider(height=20, thickness=1, color=ft.Colors.GREY_800)
            )

    round_songs = ft.Container(
        content=round_songs_list,
        expand=True,
        visible=False
    )

    return round_songs