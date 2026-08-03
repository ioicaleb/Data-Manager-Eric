import flet as ft
from data_processing.search_processor import find_song_by_id

def generate_player_stats(player_stats_data, is_mobile=False):
    """
    Renders an in-memory deep-dive analytics landing board detailing a user's 
    accumulated records, round records, top artists, and engagement data.
    """
    def create_nested_song_card(song_data) -> ft.Container:
        """Standardizes song card hierarchy, inner padding, and voter logs safely."""
        if not song_data:
            return ft.Container()
            
        voter_list_column = ft.Column(spacing=4)
        
        for voter in song_data.get("voters", []):
            voter_name = voter.get("name", "Anonymous")
            voter_votes = voter.get("votes", 0)
            player_name_val = song_data.get("player_name", "")           
            show_votes_cond = voter_name != player_name_val and voter_votes
            voter_text_str = f"{voter_name}:  {voter_votes} pts" if show_votes_cond else f"{voter_name}"
            
            voter_info = ft.Column(
                controls=[ft.Text(voter_text_str, size=14 if not is_mobile else 12, color=ft.Colors.GREY_400, no_wrap=False)],
                spacing=2
            )
            
            if voter.get("comment"):
                voter_info.controls.append(
                    ft.Container(
                        content=ft.Text(
                            f"💬 \"{voter.get('comment')}\"",
                            size=14 if not is_mobile else 12,
                            italic=True,
                            color=ft.Colors.GREY_500
                        ),
                        margin=ft.Margin(12, 0, 8, 0)
                    )
                )
            voter_list_column.controls.append(voter_info)

        voter_container =  ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(f"🎵 {song_data.get('name', 'Unknown Track')}", size=24 if not is_mobile else 16, weight=ft.FontWeight.W_600, no_wrap=False),
                    ft.Text(f"Artist: {song_data.get('artist', 'Unknown')}   |   Album: {song_data.get('album', 'Unknown')}", size=18 if not is_mobile else 12, color=ft.Colors.GREY_400, no_wrap=False),
                    ft.Text(f"Comment: {song_data.get('user_comment', 'Unknown')}", size=18 if not is_mobile else 12, no_wrap=False) if song_data.get('user_comment') else None, 
                    ft.Text(f"Total Votes: {song_data.get('votes', 0)} pts", size=18 if not is_mobile else 12, weight=ft.FontWeight.W_500, no_wrap=False),
                    ft.Container(
                        content=voter_list_column,
                        margin=ft.Margin(20, 5, 0, 10)if not is_mobile else ft.Margin(10, 5, 0, 10)
                    )
                ],
                spacing=4
            ),
            margin=ft.Margin(0, 0, 0, 15)
        )

        voter_container.content.controls = [c for c in voter_container.content.controls if c is not None]

        return voter_container

    favorite_player_container = ft.Container(
        content=ft.Row([
            ft.Icon(ft.Icons.FAVORITE, color=ft.Colors.RED_400, size=24 if not is_mobile else 18),
            ft.Text(f"Favorite Player: {player_stats_data.get('favorite_player', 'None Checked')}", size=20 if not is_mobile else 14, weight=ft.FontWeight.BOLD, no_wrap=False)
        ]),
        margin=ft.Margin(bottom=15)
    )

    top_player_container = ft.Container(
        content=ft.Row([
            ft.Icon(ft.Icons.THUMB_UP, color=ft.Colors.BLUE_400, size=24 if not is_mobile else 18),
            ft.Text(f"Most Favorited Player: {player_stats_data.get('top_player', 'None Checked')}", size=20 if not is_mobile else 14, weight=ft.FontWeight.BOLD, no_wrap=False)
        ]),
        margin=ft.Margin(bottom=15)
    )

    points_per_vote_container = ft.Container(
        content=ft.Row([
            ft.Icon(ft.Icons.HOW_TO_VOTE, color=ft.Colors.GREEN_400, size=24 if not is_mobile else 18),
            ft.Text(f"Points per Vote: {player_stats_data.get('points_per_vote', '0.0')}", size=20 if not is_mobile else 14, weight=ft.FontWeight.BOLD, no_wrap=False)
        ]),
        margin=ft.Margin(bottom=15)
    )

    number_of_comments_container = ft.Container(
        content=ft.Row([
            ft.Icon(ft.Icons.MESSAGE, color=ft.Colors.PURPLE_400, size=24 if not is_mobile else 18),
            ft.Text(f"Number of Comments Left: {player_stats_data.get('comments', 0)} Comments", size=20 if not is_mobile else 14, weight=ft.FontWeight.BOLD, no_wrap=False, max_lines=2, overflow=ft.TextOverflow.VISIBLE)
        ]),
        margin=ft.Margin(bottom=15)
    )

    best_song_id = player_stats_data.get("best_song")
    best_song = find_song_by_id(best_song_id) if best_song_id else None
    
    if best_song:
        best_song_view = ft.Column(
            controls=[
                ft.Row([
                    ft.Text(f"🏆 Best Song: {best_song.get('name', 'Unknown')}", size=24 if not is_mobile else 18, weight=ft.FontWeight.BOLD, color="amber200", no_wrap=False),
                ]),
                ft.Container(
                    content=ft.Column( controls = [
                        ft.Text(f"Artist: {best_song.get('artist', 'Unknown')}", size=18 if not is_mobile else 14, no_wrap=False),
                        ft.Text(f"Album: {best_song.get('album', 'Unknown')}", size=18 if not is_mobile else 14, no_wrap=False),
                        ft.Text(f"Comment: {best_song.get('user_comment', '')}", size=18 if not is_mobile else 14, no_wrap=False) if best_song.get('user_comment') else None,
                        ft.Text(f"Votes: {best_song.get('votes', 0)} pts", size=18 if not is_mobile else 14, weight=ft.FontWeight.BOLD, color="greenAccent200", no_wrap=False),
                    ], spacing=2),
                    margin=ft.Margin(30, 0, 0, 0)
                )
            ],
            spacing=5
        )
    else:
        best_song_view = ft.Text("No songs found.", italic=True, size=18 if not is_mobile else 14, color="grey", no_wrap=False)

    best_song_view.controls[1].content.controls = [c for c in best_song_view.controls[1].content.controls if c is not None]
    best_song_container = ft.Container(content=best_song_view, margin=ft.Margin(bottom=15))

    best_round = player_stats_data.get("best_round", {})
    round_score = best_round.get("score", 0)
    round_number = best_round.get("round_number", "?")

    best_round_songs_column = ft.Column(spacing=10)
    for song_id in best_round.get("songs", []):
        song_obj = find_song_by_id(song_id)
        if song_obj:
            best_round_songs_column.controls.append(create_nested_song_card(song_obj))

    best_round_container = ft.Container(
        content=ft.Column(
            controls=[
                ft.Row([
                    ft.Icon(ft.Icons.ALBUM),
                    ft.Text(f"Best Round Performance: Round {round_number} — {best_round.get('title', 'Unknown Title')}", size=20 if not is_mobile else 16, weight=ft.FontWeight.BOLD, no_wrap=False),
                ]),
                ft.Text(f"Score: {round_score} Points", size=16 if not is_mobile else 12, weight=ft.FontWeight.W_600, color=ft.Colors.BLUE_400, no_wrap=False),
                ft.Container(content=best_round_songs_column, margin=ft.Margin(20, 5, 0, 0))
            ],
            spacing=5
        ),
        margin=ft.Margin(bottom=15)
    )

    favorite_artist_dict = player_stats_data.get("favorite_artist", ["Unknown Artist", {"appearances": 0, "songs": []}])
    favorite_artist_name = favorite_artist_dict[0] if len(favorite_artist_dict) > 0 else "Unknown"
    favorite_artist_data = favorite_artist_dict[1] if len(favorite_artist_dict) > 1 else {}

    fav_artist_songs_column = ft.Column(spacing=10)
    if isinstance(favorite_artist_data, dict):
        for song_entry in favorite_artist_data.get("songs", []):
            fav_artist_songs_column.controls.append(create_nested_song_card(song_entry))

    favorite_artist_container = ft.Container(
        content=ft.Column(
            controls=[
                ft.Row([
                    ft.Icon(ft.Icons.QUEUE_MUSIC, color=ft.Colors.ORANGE_400),
                    ft.Text(f"Favorite Artist: {favorite_artist_name}", size=20 if not is_mobile else 16, weight=ft.FontWeight.BOLD, no_wrap=False),
                ]),
                ft.Text(f"Appearances: {favorite_artist_data.get('appearances', 0)} times", size=16 if not is_mobile else 12, weight=ft.FontWeight.W_600, no_wrap=False),
                ft.Container(content=fav_artist_songs_column, margin=ft.Margin(20, 5, 0, 0))
            ],
            spacing=5
        ),
        margin=ft.Margin(bottom=15)
    )

    top_artist_dict = player_stats_data.get("top_artist", ["Unknown Artist", {"votes": 0, "songs": []}])
    top_artist_name = top_artist_dict[0] if len(top_artist_dict) > 0 else "Unknown"
    top_artist_data = top_artist_dict[1] if len(top_artist_dict) > 1 else {}

    top_artist_songs_column = ft.Column(spacing=10)
    if isinstance(top_artist_data, dict):
        for song_entry in top_artist_data.get("songs", []):
            top_artist_songs_column.controls.append(create_nested_song_card(song_entry))

    top_artist_container = ft.Container(
        content=ft.Column(
            controls=[
                ft.Row([
                    ft.Icon(ft.Icons.STAR_FILL if hasattr(ft.Icons, "STAR_FILL") else ft.Icons.STAR, color=ft.Colors.YELLOW_400),
                    ft.Text(f"Top Artist: {top_artist_name}", size=20 if not is_mobile else 16, weight=ft.FontWeight.BOLD, no_wrap=False),
                ]),
                ft.Text(f"Total Points: {top_artist_data.get('votes', 0)} pts", size=16 if not is_mobile else 12, weight=ft.FontWeight.W_600, no_wrap=False),
                ft.Container(content=top_artist_songs_column, margin=ft.Margin(left=20, top=5))
            ],
            spacing=5
        ),
        margin=ft.Margin(bottom=15)
    )

    player_stats_list = ft.ListView(
        expand=True,
        spacing=15,
        padding=ft.Padding(20, 0, 20, 20),
        scroll=ft.ScrollMode.AUTO,
        controls=[
            ft.Card(content=ft.Container(content=favorite_player_container, padding=12)),
            ft.Card(content=ft.Container(content=top_player_container, padding=12)),
            ft.Card(content=ft.Container(content=points_per_vote_container, padding=12)),
            ft.Card(content=ft.Container(content=number_of_comments_container, padding=12)),
            ft.Card(content=ft.Container(content=best_song_container, padding=12)),
            ft.Card(content=ft.Container(content=best_round_container, padding=12)),
            ft.Card(content=ft.Container(content=favorite_artist_container, padding=12)),
            ft.Card(content=ft.Container(content=top_artist_container, padding=12))
        ],
    )

    player_stats = ft.Container(
        content=player_stats_list,
        expand=True,
        height = 600,
        width = 360 if is_mobile else 900,
        visible=False
    )

    return player_stats