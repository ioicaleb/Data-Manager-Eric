import flet as ft
from data_processing.search_processor import find_song_by_id

def generate_player_stats(player_stats_data):
    def create_nested_song_card(song_data) -> ft.Column:
        """Standardizes song card hierarchy, inner padding, and voter logs."""
        voter_list_column = ft.Column(spacing=4)
        
        for voter in song_data.get("voters", []):
            voter_name = voter.get("name")
            voter_votes = voter.get("votes")
            player_name_val = song_data.get("player_name")
            
            show_votes_cond = voter_name != player_name_val and voter_votes
            voter_text_str = f"{voter_name}:  {voter_votes}" if show_votes_cond else f"{voter_name}"
            
            voter_info = ft.Column(
                controls=[ft.Text(voter_text_str, size=16, color=ft.Colors.GREY_400)],
                spacing=2
            )
            
            if voter.get("comment"):
                voter_info.controls.append(
                    ft.Container(
                        content=ft.Text(
                            f"- {voter.get('comment')}",
                            size=15,
                            italic=True,
                            color=ft.Colors.GREY_500
                        ),
                        margin=ft.Margin(12, 0, 8, 0)
                    )
                )
            voter_list_column.controls.append(voter_info)

        return ft.Column(
            controls=[
                ft.Text(f"🎵 {song_data.get('name')}", size=18, weight=ft.FontWeight.W_600),
                ft.Text(f"Artist: {song_data.get('artist')}   |   Album: {song_data.get('album')}", size=15, color=ft.Colors.GREY_400),
                ft.Text(f"Total Votes: {song_data.get('votes')}", size=15, weight=ft.FontWeight.W_500),
                ft.Container(
                    content=voter_list_column,
                    margin=ft.Margin(20, 5, 0, 10)
                )
            ],
            spacing=4,
            margin=ft.Margin(0, 0, 0, 15)
        )

    favorite_player_container = ft.Container(
        content=ft.Row([
            ft.Icon(ft.CupertinoIcons.HEART_SOLID, color=ft.Colors.RED_400, size=24),
            ft.Text(f"Favorite Player: {player_stats_data.get('favorite_player')}", size=22, weight=ft.FontWeight.BOLD)
        ]),
        margin=ft.Margin(0, 0, 0, 15)
    )

    top_player_container = ft.Container(
        content=ft.Row([
            ft.Icon(ft.CupertinoIcons.HAND_THUMBSUP_FILL, color=ft.Colors.BLUE_400, size=24),
            ft.Text(f"Most Favorited Player: {player_stats_data.get('top_player')}", size=22, weight=ft.FontWeight.BOLD)
        ]),
        margin=ft.Margin(0, 0, 0, 15)
    )

    points_per_vote_container = ft.Container(
        content=ft.Row([
            ft.Icon(ft.Icons.HOW_TO_VOTE, color=ft.Colors.GREEN_400, size=24),
            ft.Text(f"Points per Vote: {player_stats_data.get('points_per_vote')}", size=22, weight=ft.FontWeight.BOLD)
        ]),
        margin=ft.Margin(0, 0, 0, 15)
    )

    number_of_comments_container = ft.Container(
            content=ft.Row([
            ft.Icon(ft.Icons.MESSAGE, color=ft.Colors.PURPLE_400, size=24),
            ft.Text(f"Number of Comments: {player_stats_data.get('comments')}", size=22, weight=ft.FontWeight.BOLD)
            ]),
            margin=ft.Margin(0, 0, 0, 15)
    )

    best_song_id = player_stats_data.get("best_song", {})
    best_song = find_song_by_id(best_song_id)
    best_song_container = ft.Container(
        content=ft.Column(
            controls=[
                ft.Row([
                    ft.Text(f"🏆 Best Song: {best_song.get('name')}", size=22, weight=ft.FontWeight.BOLD),
                ]),
                ft.Container(
                    content=ft.Column([
                        ft.Text(f"Artist: {best_song.get('artist')}", size=16),
                        ft.Text(f"Album: {best_song.get('album')}", size=16),
                        ft.Text(f"Votes: {best_song.get('votes')}", size=16),
                    ], spacing=2),
                    margin=ft.Margin(30, 0, 0, 0)
                )
            ],
            spacing=5
        ),
        margin=ft.Margin(0, 0, 0, 15)
    )

    best_round = player_stats_data.get("best_round", {})
    round_score = best_round.get("score")
    round_id = best_round.get("round_id")

    best_round_songs_column = ft.Column(spacing=10)
    for song_id in best_round.get("songs", []):
        song = find_song_by_id(song_id)
        best_round_songs_column.controls.append(create_nested_song_card(song))

    best_round_container = ft.Container(
        content=ft.Column(
            controls=[
                ft.Row([
                    ft.Icon(ft.CupertinoIcons.MUSIC_ALBUMS_FILL, color=ft.Colors.AMBER_400),
                    ft.Text(f"Best Round: Round {round_id} - {best_round.get('title', '')}", size=22, weight=ft.FontWeight.BOLD),
                ]),
                ft.Text(f"Score: {round_score}", size=18, weight=ft.FontWeight.W_600, color=ft.Colors.BLUE_400),
                ft.Container(content=best_round_songs_column, margin=ft.Margin(20, 5, 0, 0))
            ],
            spacing=5
        ),
        margin=ft.Margin(0, 0, 0, 15)
    )

    favorite_artist_dict = player_stats_data.get("favorite_artist", ["Unknown", {"appearances": 0, "songs": []}])
    favorite_artist_name = favorite_artist_dict[0]
    favorite_artist_data = favorite_artist_dict[1]

    fav_artist_songs_column = ft.Column(spacing=10)
    for song in favorite_artist_data.get("songs", []):
        fav_artist_songs_column.controls.append(create_nested_song_card(song))

    favorite_artist_container = ft.Container(
        content=ft.Column(
            controls=[
                ft.Row([
                    ft.Icon(ft.CupertinoIcons.GUITARS, color=ft.Colors.ORANGE_400),
                    ft.Text(f"Favorite Artist: {favorite_artist_name}", size=22, weight=ft.FontWeight.BOLD),
                ]),
                ft.Text(f"Appearances: {favorite_artist_data.get('appearances')}", size=18, weight=ft.FontWeight.W_600),
                ft.Container(content=fav_artist_songs_column, margin=ft.Margin(20, 5, 0, 0))
            ],
            spacing=5
        ),
        margin=ft.Margin(0, 0, 0, 15)
    )

    top_artist_dict = player_stats_data.get("top_artist", ["Unknown", {"votes": 0, "songs": []}])
    top_artist_name = top_artist_dict[0]
    top_artist_data = top_artist_dict[1]

    top_artist_songs_column = ft.Column(spacing=10)
    for song in top_artist_data.get("songs", []):
        top_artist_songs_column.controls.append(create_nested_song_card(song))

    top_artist_container = ft.Container(
        content=ft.Column(
            controls=[
                ft.Row([
                    ft.Icon(ft.CupertinoIcons.STAR_FILL, color=ft.Colors.YELLOW_400),
                    ft.Text(f"Best Artist: {top_artist_name}", size=22, weight=ft.FontWeight.BOLD),
                ]),
                ft.Text(f"Score: {top_artist_data.get('votes')}", size=18, weight=ft.FontWeight.W_600),
                ft.Container(content=top_artist_songs_column, margin=ft.Margin(20, 5, 0, 0))
            ],
            spacing=5
        ),
        margin=ft.Margin(0, 0, 0, 15)
    )

    player_stats_list = ft.ListView(
        expand=True,
        spacing=15,
        padding=ft.Padding(20, 0, 20, 20),
        scroll=ft.ScrollMode.HIDDEN,
        controls=[
            favorite_player_container,
            top_player_container,
            best_song_container,
            best_round_container,
            favorite_artist_container,
            top_artist_container,
            points_per_vote_container,
            number_of_comments_container
        ],
    )

    player_stats = ft.Container(
        content=player_stats_list,
        expand=True,
        visible=False
    )

    return player_stats