import flet as ft
import urllib.parse
from data_processing.data_processor import get_players
from data_processing.cache_manager import read_json

# Import your explicit nested stat player layout sub-tabs
from player_tabs.top_songs import generate_top_songs
from player_tabs.all_songs import generate_all_songs
from player_tabs.round_songs import generate_round_songs
from player_tabs.votes_from import generate_votes_from
from player_tabs.votes_to import generate_votes_to
from player_tabs.player_stats import generate_player_stats
from player_tabs.votes_songs import generate_votes_songs

def generate_profile_tab(page: ft.Page, return_callback):
    """
    Highly optimized interactive player profile selection portal.
    Bypasses main-thread I/O bottlenecks to maximize initial tab load speeds.
    """
    master_profile_wrapper = ft.Container(expand=True)
    profiles_list = ft.ListView(expand=True, spacing=10, padding=10)
    
    players_data = get_players() or []

    def return_to_players(e):
        profile_details_box.visible = False
        list_view_box.visible = True
        page.update()

    async def get_player_profile(player: dict):
        page.splash = ft.ProgressBar()
        page.update()

        name = player.get("name", "Unknown")
        player_stats_data = read_json(f"precomputed_stats_{name}") or {}

        page.splash = None

        back_button = ft.Button(
            content="Back to List",
            icon=ft.Icons.ARROW_BACK,
            on_click=return_to_players
        )
        
        local_img_path = player_stats_data.get("avatar_url")
        if local_img_path:
            from main import fetch_avatar_base64_raw
            
            base64_large_str = fetch_avatar_base64_raw(local_img_path)

            if base64_large_str:
                large_data_uri = f"data:image/jpeg;base64,{base64_large_str}"
                
                avatar = ft.Image(
                    src=large_data_uri,
                    width=100, 
                    height=100, 
                    fit=ft.BoxFit.COVER, 
                    border_radius=50,
                    gapless_playback=True
                )
            else:
                avatar = ft.Icon(ft.Icons.ACCOUNT_CIRCLE, size=100, color=ft.Colors.GREY_600)
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

        first_title = list(views_map.keys())[0]
        for t_key, container in views_map.items():
            container.visible = (t_key == first_title)

        def handle_menu_click(e):
            clicked_title = e.control.content.value
            is_dark_mode = page.theme_mode == ft.ThemeMode.DARK
            default_color = ft.Colors.WHITE if is_dark_mode else ft.Colors.BLACK

            for title, view_container in views_map.items():
                view_container.visible = (title == clicked_title)
            
            try:
                main_row_split = profile_view.controls[2]
                left_menu_container = main_row_split.controls[0]
                actual_menu_column = left_menu_container.content

                for button in actual_menu_column.controls:
                    if button.content.value == clicked_title:
                        button.content.color = ft.Colors.PURPLE_500
                    else:
                        button.content.color = default_color
            except Exception as loop_err:
                print(f"Menu click text tracking realignment failed: {loop_err}")
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
                main_row_split = profile_view.controls[2]
                left_menu_container = main_row_split.controls[0]
                actual_menu_column = left_menu_container.content

                for button in actual_menu_column.controls:
                    if button.content.color != ft.Colors.PURPLE_500:
                        button.content.color = default_color
            except Exception as theme_err:
                print(f"Theme change text tracking realignment failed: {theme_err}")
            page.update()
    
        theme_switch = ft.IconButton(
            icon=ft.Icons.BRIGHTNESS_4,
            on_click=toggle_theme,
            tooltip="Toggle Dark Mode"
        )

        profile_view = ft.Column(
            expand=True,
            controls=[
                ft.Row(
                    controls=[
                        back_button,
                        avatar,
                        ft.Column([
                            ft.Text(player.get('name', 'Player'), size=32, weight=ft.FontWeight.BOLD),
                            ft.Text(f"{player.get('position', '#?')} — {player.get('votes_to', 0)} Votes Received", size=20)
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
                            margin=ft.Margin(20, 0, 0, 0),
                            content=ft.Column(
                                alignment=ft.MainAxisAlignment.START,
                                spacing=15,
                                controls=[
                                    ft.TextButton(
                                        content=ft.Text(
                                            title, 
                                            size=18, 
                                            weight=ft.FontWeight.BOLD,
                                            color=ft.Colors.PURPLE_500 if title == first_title else (ft.Colors.WHITE if page.theme_mode == ft.ThemeMode.DARK else ft.Colors.BLACK)
                                        ),
                                        on_click=handle_menu_click,
                                        style=ft.ButtonStyle(padding=0)
                                    ) for title in views_map.keys()
                                ],
                            ),
                        ),
                        ft.VerticalDivider(width=40, color=ft.Colors.GREY_800),
                        ft.Container(
                            margin=ft.Margin(20, 0, 0, 0),
                            expand=True,
                            content=ft.Column(
                                expand=True,
                                controls=list(views_map.values()),
                            ),
                        )
                    ],
                ),
            ],
        )
        
        profile_details_box.content = profile_view
        list_view_box.visible = False
        profile_details_box.visible = True
        page.update()

    def create_click_handler(target_player):
        return lambda e: page.run_task(get_player_profile, target_player)

    players_iterable = []
    if isinstance(players_data, dict):
        for k, v in players_data.items():
            if isinstance(v, dict) and k != "[Left the league]":
                if "name" not in v:
                    v["name"] = k
                players_iterable.append(v)
    elif isinstance(players_data, list):
        players_iterable = [p for p in players_data if isinstance(p, dict) and p.get("name") != "[Left the league]"]

    avatar_controls_registry = {}

    for p_obj in players_iterable:
        p_name = p_obj.get("name") or p_obj.get("player") or "Unknown Player"
        p_votes = p_obj.get("votes_to", 0)
        p_rank = p_obj.get("position", "#?")

        placeholder_icon = ft.Container(
            content=ft.Icon(ft.Icons.ACCOUNT_CIRCLE, size=40, color=ft.Colors.RED_400),
            width=50,
            height=50,
            alignment=ft.Alignment.CENTER
        )
        avatar_controls_registry[p_name] = placeholder_icon

        profiles_list.controls.append(
            ft.ListTile(
                leading=placeholder_icon,
                title=ft.Text(f"{p_rank}. {p_name}", size=20, weight=ft.FontWeight.BOLD),
                subtitle=ft.Text(f"Total Votes Received: {p_votes}"),
                trailing=ft.Icon(ft.Icons.CHEVRON_RIGHT),
                on_click=create_click_handler(p_obj)
            )
        )

    async def hydrate_player_avatars_async():
        """Fetches and renders avatar image assets natively using local function lookups."""
        from main import fetch_avatar_base64_raw
        import asyncio
        
        for name, container_control in avatar_controls_registry.items():
            try:
                p_stats = read_json(f"precomputed_stats_{name}") or {}
                img_url = p_stats.get("avatar_url")
                
                if img_url:
                    base64_data_str = fetch_avatar_base64_raw(img_url)
                    
                    if base64_data_str:
                        data_uri_string = f"data:image/jpeg;base64,{base64_data_str}"
                        
                        container_control.content = ft.Image(
                            src=data_uri_string,
                            fit=ft.BoxFit.COVER,      
                            width=50,                  
                            height=50,                 
                            border_radius=25, 
                            gapless_playback=True      
                        )
                        container_control.update()
                        
                await asyncio.sleep(0.01)
                
            except Exception as err:
                print(f"Async image layout skip for {name}: {err}")


    page.run_task(hydrate_player_avatars_async)

    list_view_box = ft.Container(
        content=ft.Row(
            controls=[
                ft.Column(
                    controls=[profiles_list],
                    width=500,
                    expand=False,
                    scroll=ft.ScrollMode.ALWAYS
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            expand=True
        ),
        expand=True,
        visible=True
    )
    
    profile_details_box = ft.Container(expand=True, visible=False)

    master_profile_wrapper.content = ft.Column(
        expand=True,
        controls=[list_view_box, profile_details_box]
    )
    
    return master_profile_wrapper
