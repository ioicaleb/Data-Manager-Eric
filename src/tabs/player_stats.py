import asyncio
import flet as ft
from data_processing.data_processor import get_players
from data_processing.cache_manager import read_json

from player_tabs.top_songs import generate_top_songs
from player_tabs.all_songs import generate_all_songs
from player_tabs.round_songs import generate_round_songs
from player_tabs.votes_from import generate_votes_from
from player_tabs.votes_to import generate_votes_to
from player_tabs.player_stats import generate_player_stats
from player_tabs.votes_songs import generate_votes_songs


async def generate_profile_tab(page: ft.Page, return_callback, progress_callback=None):
    from main import fetch_avatar_base64_raw

    async def _report(fraction: float, message: str):
        if progress_callback:
            progress_callback(fraction, message)
        await asyncio.sleep(0)

    is_mobile = (page.width or 1200) < 700

    master_profile_wrapper = ft.Container(expand=True)
    profiles_list = ft.ListView(expand=True, spacing=10, padding=10)

    await _report(0.0, "Loading player roster...")
    players_data = get_players() or []

    players_iterable = []
    if isinstance(players_data, dict):
        for k, v in players_data.items():
            if isinstance(v, dict) and k != "[Left the league]":
                if "name" not in v:
                    v["name"] = k
                players_iterable.append(v)
    elif isinstance(players_data, list):
        players_iterable = [p for p in players_data if isinstance(p, dict) and p.get("name") != "[Left the league]"]

    def _load_player_data(p_obj):
        name = p_obj.get("name") or p_obj.get("player") or "Unknown Player"
        stats = read_json(f"precomputed_stats_{name}") or {}
        avatar_url = stats.get("avatar_url")
        avatar_b64 = fetch_avatar_base64_raw(avatar_url) if avatar_url else ""
        return name, stats, avatar_b64

    player_stats_cache = {}
    avatar_cache = {}
    total_players = len(players_iterable)

    if players_iterable:
        await _report(0.05, f"Fetching player photos & stats for {total_players} players...")
        tasks = [asyncio.to_thread(_load_player_data, p) for p in players_iterable]
        completed = 0
        for coro in asyncio.as_completed(tasks):
            name, stats, avatar_b64 = await coro
            player_stats_cache[name] = stats
            avatar_cache[name] = avatar_b64
            completed += 1
            await _report(
                0.05 + 0.55 * (completed / total_players),
                f"Fetching player photos & stats — {completed}/{total_players}"
            )

    def return_to_players(e):
        profile_details_box.visible = False
        list_view_box.visible = True
        page.update()

    def show_player_profile(player_name):
        view = player_profiles_map.get(player_name)
        if view is None:
            return
        profile_details_box.content = view
        list_view_box.visible = False
        profile_details_box.visible = True
        page.update()

    def create_click_handler(target_name):
        return lambda e: show_player_profile(target_name)

    def build_player_profile_view(player: dict, player_stats_data: dict, avatar_b64: str):
        name = player.get("name", "Unknown")

        back_button = ft.Button(
            content="Back to List",
            icon=ft.Icons.ARROW_BACK,
            on_click=return_to_players
        )

        avatar_size = 64 if is_mobile else 100
        if avatar_b64:
            avatar = ft.Image(
                src=f"data:image/jpeg;base64,{avatar_b64}",
                width=avatar_size,
                height=avatar_size,
                fit=ft.BoxFit.COVER,
                border_radius=avatar_size // 2,
                gapless_playback=True
            )
        else:
            avatar = ft.Icon(ft.Icons.ACCOUNT_CIRCLE, size=avatar_size, color=ft.Colors.GREY_600)

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

        menu_dropdown_ref = {}

        def handle_menu_click(e):
            clicked_title = e.control.content.value if not is_mobile else e.control.value

            for title, view_container in views_map.items():
                view_container.visible = (title == clicked_title)

            if is_mobile:
                page.update()
                return

            try:
                main_row_split = profile_view.controls[2]
                left_menu_container = main_row_split.controls[0]
                actual_menu_column = left_menu_container.content

                for button in actual_menu_column.controls:
                    button.content.color = ft.Colors.PURPLE_500 if button.content.value == clicked_title else None
            except Exception as loop_err:
                print(f"Menu click text tracking realignment failed: {loop_err}")
                e.control.content.color = ft.Colors.PURPLE_500

            page.update()

        header_row = ft.Row(
            controls=[
                back_button,
                avatar,
                ft.Column([
                    ft.Text(player.get('name', 'Player'), size=22 if is_mobile else 32, weight=ft.FontWeight.BOLD),
                    ft.Text(
                        f"{player.get('position', '#?')} — {player.get('votes_to', 0)} Votes Received",
                        size=14 if is_mobile else 20
                    )
                ])
            ],
            spacing=20,
            wrap=True
        )

        if is_mobile:
            section_picker = ft.Dropdown(
                value=first_title,
                options=[ft.dropdown.Option(title) for title in views_map.keys()],
                on_change=handle_menu_click,
                expand=True
            )

            profile_view = ft.Column(
                expand=True,
                controls=[
                    header_row,
                    ft.Divider(height=20, color=ft.Colors.GREY_800),
                    section_picker,
                    ft.Container(height=10),
                    ft.Container(
                        expand=True,
                        content=ft.Column(expand=True, controls=list(views_map.values())),
                    )
                ],
            )
        else:
            profile_view = ft.Column(
                expand=True,
                controls=[
                    header_row,
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
                                                color=ft.Colors.PURPLE_500 if title == first_title else None
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

        return profile_view

    player_profiles_map = {}
    for idx, p_obj in enumerate(players_iterable, start=1):
        name = p_obj.get("name") or p_obj.get("player") or "Unknown Player"
        player_profiles_map[name] = build_player_profile_view(
            p_obj, player_stats_cache.get(name, {}), avatar_cache.get(name, "")
        )
        if total_players:
            await _report(
                0.60 + 0.35 * (idx / total_players),
                f"Building player profile views — {idx}/{total_players}"
            )

    await _report(0.97, "Finishing up player profiles...")

    for p_obj in players_iterable:
        p_name = p_obj.get("name") or p_obj.get("player") or "Unknown Player"
        p_votes = p_obj.get("votes_to", 0)
        p_rank = p_obj.get("position", "#?")

        avatar_b64 = avatar_cache.get(p_name, "")
        if avatar_b64:
            leading_control = ft.Image(
                src=f"data:image/jpeg;base64,{avatar_b64}",
                fit=ft.BoxFit.COVER,
                width=50,
                height=50,
                border_radius=25,
                gapless_playback=True
            )
        else:
            leading_control = ft.Icon(ft.Icons.ACCOUNT_CIRCLE, size=40, color=ft.Colors.RED_400)

        profiles_list.controls.append(
            ft.ListTile(
                leading=ft.Container(content=leading_control, width=50, height=50, alignment=ft.Alignment.CENTER),
                title=ft.Text(f"{p_rank}. {p_name}", size=20, weight=ft.FontWeight.BOLD),
                subtitle=ft.Text(f"Total Votes Received: {p_votes}"),
                trailing=ft.Icon(ft.Icons.CHEVRON_RIGHT),
                on_click=create_click_handler(p_name)
            )
        )

    list_view_box = ft.Container(
        content=ft.Row(
            controls=[
                ft.Column(
                    controls=[profiles_list],
                    width=None if is_mobile else 500,
                    expand=is_mobile,
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