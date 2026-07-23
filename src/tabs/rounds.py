import flet as ft
from data_processing.search_processor import get_rounds, find_song_by_id

def generate_rounds_tab(page: ft.Page):
    rounds_data = get_rounds()
    views_map = {}

    sort_newest = False
    current_selected_title = ""
    
    for round_item in rounds_data:
        round_id = round_item["round_number"]
        round_name = round_item["title"]

        round_header = ft.Column(
            controls = [
                ft.Text(round_id, size=64, weight=ft.FontWeight.BOLD),
                ft.Text(f"{round_name} - {round_item.get('description')}", size=20, expand= True)
            ]
        )

        round_info = ft.Column(
            controls=[],
            spacing=10,
            expand=True
        )

        song_details = ft.Container(
            content = ft.Column(
                controls=[], 
                spacing=10,
                scroll= ft.ScrollMode.HIDDEN
            ),
            expand= True
        )
        
        round_songs = ft.Container(
            content= song_details,
            expand=True,
        )

        for submission in round_item["submissions"]:
            song = find_song_by_id(submission)
            song_info = ft.Column(
                controls=[
                    ft.Text(f"{song.get('name')}", size=20, weight=ft.FontWeight.W_500),
                    ft.Text(f"Artist: {song.get('artist')}", size=18),
                    ft.Text(f"Album: {song.get('album')}", size=18),
                    ft.Text(f"Submitted By: {song.get('player_name')}", size=18),
                    ft.Text(f"Votes: {song.get('votes')}", size=18),
                ],
                spacing=2
            )
            song_details.content.controls.append(song_info)
        
        round_info.controls.append(round_songs)

        round_view = ft.Container(
            content = ft.Column(
                controls= [ 
                    ft.Column(
                        controls=[round_header, ft.Container(height=2), round_info],
                        spacing=10,
                        margin = ft.Margin(10, 0, 0, 0),
                        expand= True
                    ),
                ],
            ),
            visible = False, 
            expand =True
        )
        
        winner_list = round_item.get("winner", [])
        winner_count = len(winner_list)

        if winner_count == 0:
            winners = "Winner: Pending"
        elif winner_count == 1:
            winners = f"Winner: {winner_list[0]}"
        elif winner_count == 2:
            winners = f"Winners: {winner_list[0]} and {winner_list[1]}"
        else:
            winners = f"Winners: {', '.join(winner_list[:-1])}, and {winner_list[-1]}"
            
        round_header.controls.append(ft.Text(f"{winners}", size=24))
        round_header.controls.append(ft.Divider(thickness = 1, color=ft.Colors.GREY_100))

        views_map[f"Round {round_item['round_number']} - {round_item['title']}"] = round_view


    if views_map:
        current_selected_title = [list(views_map.keys())[0]]
        views_map[current_selected_title[0]].visible = True

    content_stack = ft.Stack(
        controls=list(views_map.values()),
        expand=True
    )

    page.update()
        
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
        except (IndexError, AttributeError):
            if e.control.content:
                e.control.content.color = ft.Colors.PURPLE_500
        
        page.update()

    def create_menu_button(title):
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

    def search_and_sort_rounds(e=None):
        """Filters the menu keys based on text search and orders them by round number."""
        keyword = search_input.value.strip().lower()
        navigation_menu.controls.clear()
        
        # Sort keys based on round number embedded in the title string
        # Expected title format: "Round X - Title Here"
        def extract_round_num(title_str):
            try:
                return int(title_str.split(" - ")[0].replace("Round ", ""))
            except ValueError:
                return 0

        sorted_titles = sorted(
            views_map.keys(), 
            key=extract_round_num, 
            reverse=sort_newest
        )

        for title in sorted_titles:
            if not keyword or keyword in title.lower():
                navigation_menu.controls.append(create_menu_button(title))
        navigation_menu.update()

    def toggle_sort(e):
        """Flips the sort direction state and updates button icon + UI menu."""
        nonlocal sort_newest
        sort_newest = not sort_newest
        if sort_newest:
            sort_button.icon = ft.Icons.ARROW_DOWNWARD
            sort_button.content.value = "Sorted by: Oldest First"
        else:
            sort_button.icon = ft.Icons.ARROW_UPWARD
            sort_button.content.value = "Sorted by: Newest First"
        sort_button.update()
        search_and_sort_rounds(None)

    navigation_menu = ft.Column(
        controls=[],
        alignment=ft.MainAxisAlignment.START,
        spacing=15,
        scroll= ft.ScrollMode.HIDDEN,
        expand = True
    )

    def create_menu_button(title):
        return ft.TextButton(
            content=ft.Text(
                title, 
                size=24, 
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.ON_SURFACE,
            ),
            on_click=handle_menu_click,
            style=ft.ButtonStyle(padding=0)
    )

    for title in views_map.keys():
        navigation_menu.controls.append(create_menu_button(title))

    def search_rounds(e = None):
        keyword = search_input.value.strip().lower()
        navigation_menu.controls.clear()
        for title in views_map.keys():
            if not keyword or keyword.lower() in title.lower():
                navigation_menu.controls.append(create_menu_button(title))
        navigation_menu.update()

    search_input = ft.TextField(
                label = "Search round number or title",
                prefix_icon= ft.Icons.SEARCH,
                expand= True,
                on_change = search_rounds,
                on_submit = search_rounds
            )

    clear_button = ft.IconButton(
            icon = ft.Icons.CLEAR,
            tooltip = "Clear search",
            on_click = lambda _: (setattr(search_input, "value", ""), search_rounds(None))
        )

    sort_button = ft.TextButton(
        content=ft.Text("Sorted by: Newest First", weight = ft.FontWeight.W_500),
        icon=ft.Icons.ARROW_DOWNWARD,
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
        content = main_view,
        expand=True
    )
    return rounds_container