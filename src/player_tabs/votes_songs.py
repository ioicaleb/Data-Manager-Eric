import flet as ft
from data_processing.search_processor import find_song_by_id

def generate_votes_songs(player_stats_data, player_name):
    """
    Renders an in-memory sub-tab ledger illustrating the specific songs
    the selected player voted for, along with their assigned scores and comments.
    """
    vote_songs_data = player_stats_data.get("votes_songs") or []
    
    
    votes_songs_list = ft.Container(
        content=ft.Column(
            controls=[], 
            scroll=ft.ScrollMode.HIDDEN,
            spacing=20
        ),
        border_radius=10,
        expand=True,
    )
    
    for song_id in vote_songs_data:
        song = find_song_by_id(song_id)
        if not song:
            continue
            
        song_details = ft.Container(
            content=ft.Column(controls=[], spacing=10)
        )
        song_info = None
        voter_card = song.get("voters", [])
        
        for voter in voter_card:
            if voter.get("name", "").lower() == player_name.lower():
                
                song_info = ft.Column(
                    controls=[
                        ft.Text(f"🎵 {song.get('name', 'Unknown Track')}", size=24, weight=ft.FontWeight.W_500),
                        ft.Text(f"Artist: {song.get('artist', 'Unknown')}", size=18),
                        ft.Text(f"Album: {song.get('album', 'Unknown')}", size=18),
                        ft.Text(f"Submitted By: {song.get('player_name', 'Unknown')}", size=18, color="amber200"),
                        ft.Text(f"Comment: {song.get('user_comment', 'Unknown')}", size=18) if song.get('user_comment') else None,
                        ft.Text(f"Points Awarded by {player_name}: {voter.get('votes', 0)} pts", size=18, weight=ft.FontWeight.BOLD, color="greenAccent200"),
                    ],
                    spacing=3,
                    margin=ft.Margin(left=40)
                )

                song_info.controls = [c for c in song_info.controls if c is not None]
                
                if voter.get("comment"):
                    
                    song_info.controls.append(
                        ft.Container(
                            content=ft.Text(
                                f"💬 \"{voter.get('comment')}\"", 
                                size=16, 
                                italic=True, 
                                color="grey400"
                            ),
                            margin=ft.Margin(left=5, top=5)
                        )
                    )
                break
                
        if song_info:
            
            song_details.content.controls.append(song_info)
            votes_songs_list.content.controls.append(
                ft.Card(content=ft.Container(content=song_details, padding=15), expand= True)
            )
            votes_songs_list.content.controls.append(
                ft.Divider(height=10, thickness=1, color=ft.Colors.GREY_800)
            )

    votes_songs = ft.Container(
        content=votes_songs_list,
        expand=True,
        visible=False
    )

    return votes_songs