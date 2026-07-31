import flet as ft
from data_processing.search_processor import get_rounds, find_song_by_id

sort_newest = False

def generate_rounds_tab(page: ft.Page):
    """
    Renders an interactive, searchable sidebar layout displaying round themes, 
    song submissions, tracks metadata, and final point winners.
    """
    is_mobile = (page.width or 1200) < 700
    content_height = max(400, (page.height or 900) - 220)

    content_stack = ft.Stack(expand=True)
    navigation_menu = ft.Column(
        controls=[],
        alignment=ft.MainAxisAlignment.START,
        spacing=15,
        scroll=ft.ScrollMode.HIDDEN,
        height=content_height,
    )

    views_map = {}
    current_selected_title = [""]

    def handle_menu_click(e):
        clicked_title = e.control.content.value
        default_color = ft.Colors.ON_SURFACE

        for title, view_container in views_map.items():
            if title == clicked_title:
                view_container.visible = True
            else:
                view_container.visible = False
        
        try:
            for button in navigation_menu.controls:
                if isinstance(button, ft.TextButton) and button.content:
                    if button.content.value == clicked_title:
                        button.content.color = ft.Colors.PURPLE_500
                    else:
                        button.content.color = default_color
        except Exception:
            if e.control.content:
                e.control.content.color = ft.Colors.PURPLE_500
        
        page.update()

    def create_menu_button(title):
        """Generates dynamic navigation controls with color indicators."""
        is_active = (title == current_selected_title[0])
        return ft.TextButton(
            content=ft.Text(
                title, 
                size=24, 
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.PURPLE_500 if is_active else ft.Colors.ON_SURFACE,
            ),
            on_click=handle_menu_click,
            style=ft.ButtonStyle(padding=0)
        )

    def search_and_sort_rounds(e=None, initial_load=False):
        """Filters the menu keys based on text search and orders them by round number."""
        keyword = search_input.value.strip().lower() if search_input.value else ""

        navigation_menu.controls.clear()
        
        def extract_round_num(title_str):
            try:
                return int(title_str.split(" - ")[0].replace("Round ", ""))
            except (ValueError, IndexError):
                return 0

        sorted_titles = sorted(
            views_map.keys(), 
            key=extract_round_num, 
            reverse=sort_newest
        )

        for title in sorted_titles:
            if not keyword or keyword in title.lower():
                navigation_menu.controls.append(create_menu_button(title))
        
        if not initial_load:
            try:
                navigation_menu.update()
            except Exception:
                pass

    def toggle_sort(e):
        """Swaps sorting order configurations dynamically between oldest and newest round metrics."""
        global sort_newest
        
        sort_newest = not sort_newest
        
        if sort_newest:
            sort_button.content.value = "Sorted by: Newest First"
            sort_button.icon = ft.Icons.ARROW_DOWNWARD
        else:
            sort_button.content.value = "Sorted by: Oldest First"
            sort_button.icon = ft.Icons.ARROW_UPWARD
            
        search_and_sort_rounds(e=None, initial_load=False)
        sort_button.update()

    def hydrate_live_rounds_view():
        """
        Pulls fresh database parameters from memory variables.
        Safely constructs stack layouts and handles empty state protection flags.
        """
        nonlocal current_selected_title
        views_map.clear()
        content_stack.controls.clear()
        navigation_menu.controls.clear()

        rounds_data = get_rounds() or []
        
        if not rounds_data:
            empty_notice = ft.Container(
                content=ft.Text("No Completed Rounds Available Yet.", size=20, italic=True, color="grey"),
                alignment=ft.Alignment.CENTER,
                expand=True
            )
            content_stack.controls.append(empty_notice)
            return

        for round_item in rounds_data:
            round_number = round_item.get("round_number", "_")
            round_name = round_item.get("title", f"Round {round_number}")

            round_header = ft.Column(
                controls=[
                    ft.Text(str(round_number), size=36 if is_mobile else 64, weight=ft.FontWeight.BOLD),
                    ft.Text(f"{round_name} - {round_item.get('description', '')}", size=18 if is_mobile else 20)
                ]
            )
            song_details = ft.Container(
                content=ft.Column(
                    controls=[], 
                    spacing=15,
                    scroll=ft.ScrollMode.HIDDEN,
                    height=content_height
                ),
                alignment=ft.Alignment.TOP_LEFT,
                bgcolor=ft.Colors.TRANSPARENT
            )

            for submission in round_item.get("submissions", []):
                song = find_song_by_id(submission)
                if song:
                    song_info = ft.Column(
                        controls=[
                            ft.Text(f"{song.get('name', 'Unknown Track')}", size=20, weight=ft.FontWeight.W_500),
                            ft.Text(f"Artist: {song.get('artist', 'Unknown')}", size=18),
                            ft.Text(f"Album: {song.get('album', 'Unknown')}", size=18),
                            ft.Text(f"Submitted By: {song.get('player_name', 'Unknown')}", size=18),
                            ft.Text(f"Votes: {song.get('votes', 0)}", size=18),
                        ],
                        spacing=2
                    )
                    song_details.content.controls.append(song_info)
                
            winner_list = round_item.get("winner", []) or []
            winner_count = len(winner_list)

            if winner_count == 0:
                winners = "Winner: Pending"
            elif winner_count == 1:
                winners = f"Winner: {winner_list[0]}"
            elif winner_count == 2:
                winners = f"Winners: {winner_list[0]} and {winner_list[1]}"
            else:
                winners = f"Winners: {', '.join(winner_list[:-1])}, and {winner_list[-1]}"
                
            round_header.controls.append(ft.Text(f"{winners}", size=24, color="amber200"))
            round_header.controls.append(ft.Divider(thickness=1, color=ft.Colors.GREY_800))

            round_view = ft.Container(
                content=ft.Column(
                    controls=[ 
                        ft.Column(
                            controls=[round_header, ft.Container(height=2), song_details],
                            spacing=10,
                            margin=ft.Margin(10, 0, 0, 0),
                            expand=True
                        ),
                    ],
                    expand=True
                ),
                visible=False, 
                expand=True
            )

            views_map[f"Round {round_number} - {round_name}"] = round_view

        if views_map:
            current_selected_title[0] = list(views_map.keys())[0]
            views_map[current_selected_title[0]].visible = True
            content_stack.controls.extend(list(views_map.values()))
            
        search_and_sort_rounds(None, initial_load=True)

    search_input = ft.TextField(
        label="Search round number or title",
        prefix_icon=ft.Icons.SEARCH,
        expand=True,
        on_change=search_and_sort_rounds,
        on_submit=search_and_sort_rounds
    )

    clear_button = ft.IconButton(
        icon=ft.Icons.CLEAR,
        tooltip="Clear search",
        on_click=lambda _: (setattr(search_input, "value", ""), search_and_sort_rounds(None))
    )

    sort_button = ft.TextButton(
        content=ft.Text("Sorted by: Oldest First", weight=ft.FontWeight.W_500),
        icon=ft.Icons.ARROW_UPWARD,
        icon_color=ft.Colors.PURPLE_500,
        on_click=toggle_sort,
        style=ft.ButtonStyle(padding=ft.Padding(5, 0, 0, 0))
    )

    sidebar_layout = ft.Column(
        controls=[
            ft.Row(
                controls=[search_input, clear_button],
                alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            ),
            sort_button,
            navigation_menu
        ],
        spacing=10,
        expand=True
    )

    hydrate_live_rounds_view()

    if is_mobile:
        sidebar_box = ft.Container(
            content=sidebar_layout,
            height=280,
            margin=ft.Margin(10, 10, 10, 0)
        )
        main_view = ft.Column(
            controls=[
                sidebar_box,
                ft.Divider(height=10, color=ft.Colors.GREY_800),
                ft.Container(content=content_stack, expand=True, padding=ft.Padding(10, 0, 10, 10))
            ],
            expand=True,
            spacing=0
        )
    else:
        main_view = ft.Row(
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=[
                ft.Container(
                    content=sidebar_layout,
                    width=360,
                    margin=ft.Margin(20, 10, 0, 0)
                ),
                ft.VerticalDivider(width=40, color=ft.Colors.TRANSPARENT),
                content_stack
            ],
            alignment=ft.MainAxisAlignment.START,
            expand=True
        )

    rounds_container = ft.Container(
        content=main_view,
        expand=True
    )
    
    return rounds_container