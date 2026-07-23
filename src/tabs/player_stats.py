import flet as ft
from data_processing.data_processor import *
import asyncio
from player_tabs.top_songs import generate_top_songs
from player_tabs.all_songs import generate_all_songs
from player_tabs.round_songs import generate_round_songs
from player_tabs.votes_from import generate_votes_from
from player_tabs.votes_to import generate_votes_to
from player_tabs.player_stats import generate_player_stats
from player_tabs.votes_songs import generate_votes_songs

def generate_profile_tab(page: ft.Page, return_callback):
    profiles_list = ft.ListView(expand=True, spacing=10, padding=10)

    players_data = get_players()

    def return_to_players(e):
        page.controls.clear()
        return_callback(page)

    async def get_player_profile(player: dict):
        page.splash = ft.ProgressBar()
        page.update()

        name = player.get("name")

        player_stats_dict = await asyncio.to_thread(read_json, f"precomputed_stats_{name}")
        player_stats_data = player_stats_dict.get(name, {}) if player_stats_dict else {}

        page.splash = None
        page.controls.clear()

        back_button = ft.Button(
                content= "Back",
            icon=ft.Icons.ARROW_BACK,
            on_click= lambda e: (return_to_players(e))
        )
        local_img_path = player_stats_data.get("avatar_url")

        if local_img_path:
            avatar = ft.Image(
                src=local_img_path,
                width=100,
                height=100
            )
        else:
            avatar = ft.Icon(ft.Icons.ACCOUNT_CIRCLE, size=100, color=ft.Colors.GREY_600)

        top_songs = generate_top_songs(player_stats_data)
        all_songs = generate_all_songs(player_stats_data)
        round_songs = generate_round_songs(player_stats_data)
        votes_from = generate_votes_from(player_stats_data, name)
        votes_to = generate_votes_to(player_stats_data)
        player_stats = generate_player_stats(player_stats_data)
        votes_songs = generate_votes_songs(player_stats_data, name)


        views_map = {
            f"{name}'s Stats": player_stats,
            f"{name}'s Songs": all_songs,
            "Favorite Songs": top_songs,
            "Songs By Round": round_songs,
            f"Who Voted For {name}": votes_to,
            f"How {name} Voted": votes_from,
            f"Songs {name} Voted For": votes_songs
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
                                    player_stats,
                                    all_songs,
                                    top_songs,
                                    round_songs,
                                    votes_to,
                                    votes_from,
                                    votes_songs
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
                
                player_stats_dict = read_json(f"precomputed_stats_{name}") or {}

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
                        subtitle=ft.Text(f"Click to view full profile", size=16),
                        trailing=ft.Icon(ft.Icons.CHEVRON_RIGHT),
                        on_click=lambda e, p_obj=player_object: page.run_task(get_player_profile, p_obj)
                    )
                )

    elif isinstance(players_data, list):
        for player_object in players_data:
            if isinstance(player_object, dict):
                name = player_object.get("name") or player_object.get("player") or "Unknown"
                player_stats_dict = read_json(f"precomputed_stats_{name}") or {}

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
                        on_click=lambda e, p_obj=player_object: page.run_task(get_player_profile, p_obj)
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
