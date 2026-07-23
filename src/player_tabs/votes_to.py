import flet as ft
from data_processing.search_processor import find_song_by_id

def generate_votes_to(player_stats_data):
    votes_to_data = player_stats_data.get("rounds_songs") or {}

    votes_to_list = ft.Container(
        content = ft.Column(
            controls = [], 
            scroll= ft.ScrollMode.HIDDEN,
        ),
        border_radius=10,
        height= 600,
        alignment=ft.Alignment.CENTER_LEFT,
        expand = True
    )
    
    for vote_round_item in votes_to_data:
        if vote_round_item.get("songs"):
            vote_round_block = ft.Column(
                controls=[
                    ft.Text(
                        f"Round {vote_round_item.get('round_id')} - {vote_round_item.get('title')}:", 
                        size=22, 
                        weight=ft.FontWeight.BOLD
                    ),
                ],
                spacing=10,
                expand = True
            )
            song_details = ft.Container(
                content=ft.Column(controls=[], spacing=10)
            )

            for song_id in vote_round_item["songs"]:
                song = find_song_by_id(song_id)
                song_info = ft.Column(
                    controls=[
                        ft.Text(f"{song.get('name')}", size=20, weight=ft.FontWeight.W_500),
                        ft.Text(f"Artist: {song.get('artist')}", size=18),
                        ft.Text(f"Album: {song.get('album')}", size=18),
                        ft.Text(f"Votes: {song.get('votes')}", size=18)
                    ],
                    spacing = 2,
                    margin = ft.Margin(40, 0, 0, 0)
                )
                voter_list = ft.Container(
                    content = ft.Column(
                            controls=[], 
                            spacing = 2
                        ),
                        margin=ft.Margin(10,0,0,0),
                        expand = True
                    )
                for voter in song["voters"]:
                    voter_stats = ft.Text(f"{voter.get('name')}{':  ' + str(voter.get('votes')) if voter.get('name') != song.get('player_name') and voter.get('votes') else ''}", size=18)
                    voter_info = ft.Column(
                            controls = [voter_stats],
                            spacing = 2
                        )
                    if voter.get("comment"):
                        voter_info.controls.append(
                            ft.Text(
                                f"{' - ' + voter.get('comment')}",
                                size=18, 
                                italic=True,
                                margin=ft.Margin(8, 0, 8, 0)
                            )
                        )
                    
                    voter_list.content.controls.append(voter_info)
                song_info.controls.append(voter_list)
                song_details.content.controls.append(song_info)
            
            vote_round_block.controls.append(song_details)
            
            votes_to_list.content.controls.append(vote_round_block)
            
            votes_to_list.content.controls.append(
                ft.Divider(height=10, thickness=1, color=ft.Colors.GREY_800)
            )

    votes_to = ft.Container(
        content= votes_to_list,
        expand=True,
        visible=False
    )

    return votes_to