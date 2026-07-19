import flet as ft
from DataProcessing.data_processor import *

def generate_profile_tab(page: ft.Page, return_callback):
    profiles_list = ft.ListView(expand=True, spacing=10, padding=10)

    players_data = get_players()
    
    def return_to_players(e):
        page.controls.clear()
        return_callback(page, 2) 

    def get_player_profile(player: dict):
        page.controls.clear()

        back_button = ft.Button(
                content= "Back",
            icon=ft.Icons.ARROW_BACK,
            on_click= lambda e: (return_to_players(e))
        )

        player_stats_dict = read_json("precomputed_stats") or {}

        player_stats_data = player_stats_dict.get(player.get("name"), {})
        local_img_path = player_stats_data.get("avatar_url")

        if local_img_path:
            avatar = ft.Image(
                src=local_img_path,
                width=100,
                height=100
            )
        else:
            avatar = ft.Icon(ft.Icons.ACCOUNT_CIRCLE, size=100, color=ft.Colors.GREY_600)

        top_songs_list = ft.Container(
            content = ft.Column(
                controls = [], 
                scroll= ft.ScrollMode.HIDDEN,
            ),
            border_radius=10,
            alignment=ft.Alignment.CENTER_LEFT
        )

        top_songs_data = find_top_songs(player["name"])
        for song in top_songs_data:
            song_details = (f"{song.get('name')}\n"
                            f"Artist: {song.get('artist')}\n"
                            f"Album: {song.get('album')}\n"
                            f"Submitted By: {song.get('player_name')}")
            top_songs_list.content.controls.append(ft.Text(song_details, size=20))

        top_songs = ft.Container(
            content= top_songs_list,
            expand=True,
            visible=False
        )

        all_songs_list =  ft.Container(
            content = ft.Column(
                controls = [], 
                scroll= ft.ScrollMode.HIDDEN,
            ),
            border_radius=10,
            height= 600,
            alignment=ft.Alignment.CENTER_LEFT
        )
        
        all_songs_data = find_songs_by_submitter(player["name"])
        for song in all_songs_data:
            song_details = (f"{song.get('name')}\n"
                            f"Artist: {song.get('artist')}\n"
                            f"Album: {song.get('album')}\n"
                            f"Votes: {song.get('votes')}")
            all_songs_list.content.controls.append(ft.Text(song_details, size=20))
        
        all_songs = ft.Container(
            content= all_songs_list,
            expand=True,
            visible=False
        )

        round_songs_list = ft.Container(
            content=ft.Column(
                controls=[], 
                scroll=ft.ScrollMode.HIDDEN,
                spacing=20
            ),
            border_radius=10,
            height=600,
        )

        round_songs_data = find_player_songs_by_round(player["name"])

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

                for song in round_item["songs"]:
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

        votes_from_list = ft.Container(
            content = ft.Column(
                controls = [], 
                scroll= ft.ScrollMode.HIDDEN,
            ),
            border_radius=10,
            height= 600,
            expand = True
        )

        votes_from_data = find_songs_by_voter(player.get("name"))

        for song in votes_from_data:
            if song.get("player_name") != player.get("name"):
                song_details = (
                    f"{song.get('name')}\n"
                    f"Artist: {song.get('artist')}\n"
                    f"Album: {song.get('album')}\n"
                    f"Submitted By: {song.get('player_name')}")
                voters = song.get("voters")
                for voter in voters:
                    if voter["name"] == player.get("name"):
                        voter_data = voter
                        song_details += f"\nYou gave it {voter_data['votes']} votes"
                        if voter.get("comment"):
                            song_details += f"\nComment: {voter.get('comment')}"
                votes_from_list.content.controls.append(
                    ft.Container(
                        content = ft.Text(song_details, size=20),
                        width = page.width / 2
                    )
                )

        votes_from = ft.Container(
            content= votes_from_list,
            expand=True,
            visible=False
        )

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

        votes_to_data = find_player_songs_by_round(player["name"])
        
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

                for song in vote_round_item["songs"]:
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
                                    margin=ft.Margin(8, 0, 8, 0),
                                    width = page.width / 2
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

        player_stats_dict = read_json("precomputed_stats") or {}

        player_stats_data = player_stats_dict.get(player.get("name"), {})

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

        best_song = player_stats_data.get("best_song", {})
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

        best_round_dict = player_stats_data.get("best_round", {})
        round_score = best_round_dict.get("score")
        round_id = next((k for k in best_round_dict.keys() if k != "score"), None)
        best_round = best_round_dict.get(round_id, {}) if round_id else {}

        best_round_songs_column = ft.Column(spacing=10)
        for song in best_round.get("songs", []):
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

        views_map = {
            "Favorite Songs": top_songs,
            f"{player.get('name')}'s Songs": all_songs,
            "Songs By Round": round_songs,
            "How You Voted": votes_from,
            "Who Voted for You": votes_to,
            f"{player.get('name')}'s Stats": player_stats
        }

        def handle_menu_click(e):
            clicked_title = e.control.content.value

            is_dark_mode = page.theme_mode == ft.ThemeMode.DARK
            default_color = ft.Colors.WHITE if is_dark_mode else ft.Colors.BLACK

            for title, view_container in views_map.items():
                if title == clicked_title:
                    view_container.visible = True
                else:
                    view_container.visible = False
            
            try:
                main_row_split = profile_view.controls[3]
                left_menu_container = main_row_split.controls[0]
                actual_menu_column = left_menu_container.content

                for button in actual_menu_column.controls:
                    if button.content.value == clicked_title:
                        button.content.color = ft.Colors.PURPLE_500
                    else:
                        button.content.color = default_color
            except (IndexError, AttributeError):
                e.control.content.color = ft.Colors.PURPLE_500
            
            page.update()

        def toggle_theme(e):
            if page.theme_mode == ft.ThemeMode.DARK:
                page.theme_mode = ft.ThemeMode.LIGHT
                theme_switch.icon = ft.Icons.BRIGHTNESS_7
            else:
                page.theme_mode = ft.ThemeMode.DARK
                theme_switch.icon = ft.Icons.BRIGHTNESS_4

            is_dark_mode = page.theme_mode == ft.ThemeMode.DARK
            default_color = ft.Colors.WHITE if is_dark_mode else ft.Colors.BLACK
            
            try:
                main_row_split = profile_view.controls[3]
                left_menu_container = main_row_split.controls[0]
                actual_menu_column = left_menu_container.content

                for button in actual_menu_column.controls:
                    if button.content.color != ft.Colors.PURPLE_500:
                        button.content.color = default_color
            except (IndexError, AttributeError):
                e.control.content.color = ft.Colors.PURPLE_500
            page.update()
    
        theme_switch = ft.IconButton(
            icon=ft.Icons.BRIGHTNESS_4,
            on_click=toggle_theme,
            tooltip="Toggle Dark Mode"
        )
        
        profile_view = ft.Column(
            expand=True,
            controls=[
                ft.Container(
                    content=ft.Stack(
                        controls=[
                            ft.Container(
                                content=back_button,
                                margin=ft.Margin(0, 10, 0, 20),
                            ), 
                            ft.Row(
                                controls=[
                                    ft.Text("Eric the Data Manager", size=42, weight=ft.FontWeight.BOLD)
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                            ),
                            ft.Container(
                                content=theme_switch,
                                right=10,
                                top=0,
                            )
                        ],
                        height=60,
                    ),
                ),
                ft.Row(
                    controls=[
                        avatar,
                        ft.Column([
                            ft.Text(player.get('name'), size=32, weight=ft.FontWeight.BOLD),
                            ft.Text(f"{player.get('position')} - Votes: {player.get('votes_to')}", size=20)
                        ])
                    ],
                    spacing=20
                ),
                ft.Divider(height=40, color=ft.Colors.GREY_800),
                ft.Row(
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    alignment=ft.MainAxisAlignment.START,
                    expand=True,
                    controls=[
                        ft.Container(
                            margin=ft.Margin(60, 0, 0, 0),
                            content=ft.Column(
                                alignment=ft.MainAxisAlignment.START,
                                spacing=15,
                                controls=[
                                    ft.TextButton(
                                        content=ft.Text(
                                            title, 
                                            size=24, 
                                            weight=ft.FontWeight.BOLD,
                                            color=ft.Colors.WHITE if page.theme_mode == ft.ThemeMode.DARK else ft.Colors.BLACK
                                        ),
                                        on_click=handle_menu_click,
                                        style=ft.ButtonStyle(padding=0)
                                    ) for i, title in enumerate(views_map.keys())
                                ],
                            ),
                        ),
                        ft.VerticalDivider(width=40, color=ft.Colors.TRANSPARENT),
                        ft.Container(
                            margin=ft.Margin(80, 0, 0, 0),
                            expand= True,
                            content=ft.Column(
                                expand = True,
                                controls=[
                                    top_songs,
                                    all_songs,
                                    round_songs,
                                    votes_from,
                                    votes_to,
                                    player_stats
                                ],
                            ),
                        )
                    ],
                ),
            ],
        )
        
        page.add(profile_view)
        page.update()
    
    if isinstance(players_data, dict):
        for name, player_object in players_data.items():
            if isinstance(player_object, dict):
                if "name" not in player_object:
                    player_object["name"] = name
                
                player_stats_dict = read_json("precomputed_stats") or {}

                player_stats_data = player_stats_dict.get(name, {})

                local_img_path = player_stats_data.get("avatar_url")

                if local_img_path:            
                    avatar = ft.Container(
                        content= ft.Image(
                            src=local_img_path,
                            fit="cover",
                            border_radius=25,
                            width=80
                        ),
                        width=80,
                        border_radius=40,
                        border=ft.BorderSide(2, ft.Colors.RED_300)
                    )
                else:
                    avatar = ft.Icon(
                        ft.Icons.ACCOUNT_CIRCLE, 
                        width=80, 
                        color=ft.Colors.RED_500
                    )
                
                profiles_list.controls.append(
                    ft.ListTile(
                        leading=avatar,
                        title=ft.Text(str(name), size=22, weight=ft.FontWeight.BOLD),
                        subtitle=ft.Text(f"Votes: {player_object.get('votes_to', 0)} • Click to view full profile", size=16),
                        trailing=ft.Icon(ft.Icons.CHEVRON_RIGHT),
                        on_click=lambda e, p_obj=player_object: get_player_profile(p_obj)
                    )
                )

    elif isinstance(players_data, list):
        for player_object in players_data:
            if isinstance(player_object, dict):
                name = player_object.get("name") or player_object.get("player") or "Unknown"
                player_stats_dict = read_json("precomputed_stats") or {}

                player_stats_data = player_stats_dict.get(name, {})

                local_img_path = player_stats_data.get("avatar_url")

                if local_img_path:            
                    avatar = ft.Container(
                        content= ft.Image(
                            src=local_img_path,
                            fit="cover",
                            border_radius=25,
                            width=80
                        ),
                        width=80,
                        border_radius=40,
                        border=ft.BorderSide(2, ft.Colors.RED_500)
                    )
                else:
                    avatar = ft.Container(
                        content = ft.Icon(
                            ft.Icons.PERSON, 
                            color=ft.Colors.RED_300,
                            width = 80
                        ),
                        width=80,
                        height = 80,
                        border_radius=40,
                        border=ft.BorderSide(2, ft.Colors.RED_500)
                    )

                
                profiles_list.controls.append(
                    ft.ListTile(
                        leading=avatar,
                        title=ft.Text(name, size=22, weight=ft.FontWeight.BOLD),
                        subtitle=ft.Text(f"Votes: {player_object.get('votes_to', 0)} • Click to view full profile", size=16),
                        trailing=ft.Icon(ft.Icons.CHEVRON_RIGHT),
                        on_click=lambda e, p_obj=player_object: get_player_profile(p_obj)
                    )
                )

    profiles_container = ft.Container(
        content=ft.Row(
            controls=[
                ft.Column(
                    controls=[profiles_list],
                    width=500,
                    expand=False,
                    scroll=ft.ScrollMode.HIDDEN
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            expand = True
        ),
        expand=True
    )

    return profiles_container
