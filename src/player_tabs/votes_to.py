import flet as ft
from data_processing.search_processor import find_song_by_id

def generate_votes_to(player_stats_data):
    """
    Renders an in-memory sub-tab matrix display illustrating all votes and comments 
    submitted to a specific player's tracks throughout the music league season.
    """
    votes_to_data = player_stats_data.get("rounds_songs") or {}

    votes_to_list = ft.Container(
        content=ft.Column(
            controls=[], 
            scroll=ft.ScrollMode.HIDDEN,
        ),
        border_radius=10,
        alignment=ft.Alignment.CENTER_LEFT,
        expand=True
    )
    
    if isinstance(votes_to_data, dict):
        iterations = votes_to_data.values()
    else:
        iterations = votes_to_data if votes_to_data else []

    iterations = sorted(iterations, key = lambda x: x['round_number'])

    for vote_round_item in iterations:
        if isinstance(vote_round_item, dict) and vote_round_item.get("songs"):
            vote_round_block = ft.Column(
                controls=[
                    ft.Text(
                        f"Round {vote_round_item.get('round_number', '?')} — {vote_round_item.get('title', 'Unknown Overview')}:", 
                        size=22, 
                        weight=ft.FontWeight.BOLD,
                        color="purple100"
                    ),
                ],
                spacing=10,
                expand=True
            )
            song_details = ft.Container(
                content=ft.Column(controls=[], spacing=10, expand = True)
            )

            for song_id in vote_round_item["songs"]:
                song = find_song_by_id(song_id)
                if not song:
                    continue

                song_info = ft.Column(
                    controls=[
                        ft.Text(f"🎵 {song.get('name', 'Unknown Title')}", size=24, weight=ft.FontWeight.W_500, color="amber100"),
                        ft.Text(f"Artist: {song.get('artist', 'Unknown')}", size=18),
                        ft.Text(f"Album: {song.get('album', 'Unknown')}", size=18),
                        ft.Text(f"Comment: {song.get('user_comment')}", size=18) if song.get('user_comment', '').strip() else None,
                        ft.Text(f"Score: {song.get('votes', 0)} Points", size=18, weight=ft.FontWeight.BOLD)
                    ],
                    spacing=3,
                    margin=ft.Margin(left=40)
                )
                song_info.controls = [c for c in song_info.controls if c is not None]
                
                voter_list = ft.Container(
                    content=ft.Column(
                        controls=[], 
                        spacing=4
                    ),
                    margin=ft.Margin(left=10),
                    expand=True
                )
                
                for voter in song.get("voters", []):
                    v_name = voter.get('name', 'Anonymous')
                    v_points = voter.get('votes', 0)
                    s_submitter = song.get('player_name', '')

                    display_text = f"{v_name}"
                    if v_name != s_submitter and v_points:
                        display_text += f":  {v_points} pts"

                    voter_stats = ft.Text(display_text, size=15, weight=ft.FontWeight.W_500)
                    voter_info = ft.Column(
                        controls=[voter_stats],
                        spacing=2
                    )
                    
                    if voter.get("comment"):
                        voter_info.controls.append(
                            ft.Container(
                                content=ft.Text(
                                    f"💬 \"{voter.get('comment')}\"",
                                    size=15, 
                                    italic=True,
                                    color="grey400"
                                ),
                                margin=ft.Margin(left=15, right=10, bottom=5)
                            )
                        )
                    
                    voter_list.content.controls.append(voter_info)
                    
                song_info.controls.append(voter_list)
                song_details.content.controls.append(ft.Card(content=ft.Container(content=song_info, padding=12)))
            
            vote_round_block.controls.append(song_details)
            votes_to_list.content.controls.append(vote_round_block)
            votes_to_list.content.controls.append(
                ft.Divider(height=20, thickness=1, color=ft.Colors.GREY_800)
            )

    votes_to = ft.Container(
        content=votes_to_list,
        expand=True,
        visible=False
    )

    return votes_to