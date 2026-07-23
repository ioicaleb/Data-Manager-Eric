import flet as ft
from data_processing.search_processor import find_song_by_id

def generate_votes_songs(player_stats_data, player_name):
    vote_songs_data = player_stats_data.get("votes_songs") or {}
    
    votes_songs_list = ft.Container(
        content=ft.Column(
            controls=[], 
            scroll=ft.ScrollMode.HIDDEN,
            spacing=20
        ),
        border_radius=10,
        height=600,
    )
    
    for song_id in vote_songs_data:
        song_details = ft.Container(
            content=ft.Column(controls=[], spacing=10)
        )
        song_info = None
        song = find_song_by_id(song_id)
        voter_card = song.get("voters")
        for voter in voter_card:
            if voter.get("name") == player_name:

                song_info = ft.Column(
                    controls=[
                        ft.Text(f"{song.get('name')}", size=20, weight=ft.FontWeight.W_500),
                        ft.Text(f"Artist: {song.get('artist')}", size=18),
                        ft.Text(f"Album: {song.get('album')}", size=18),
                        ft.Text(f"Votes: {voter.get('votes')}", size=18),
                    ],
                    spacing = 2,
                    margin = ft.Margin(40, 0, 0, 0)
                )
                if voter.get("comment"):
                    song_info.controls.append(ft.Text(f"Comment: {voter.get('comment')}", size=18))
                break
        if(song_info):
            song_details.content.controls.append(song_info)
            votes_songs_list.content.controls.append(song_details)
            votes_songs_list.content.controls.append(
            ft.Divider(height=10, thickness=1, color=ft.Colors.GREY_800)
        )

    votes_songs = ft.Container(
        content= votes_songs_list,
        expand=True,
        visible=False
    )

    return votes_songs