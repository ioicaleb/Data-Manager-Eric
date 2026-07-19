import flet as ft
from DataProcessing.search_processor import get_rounds, find_song_by_id

def generate_rounds_tab(page: ft.Page):
    rounds_data = get_rounds()
    views_map = {}
    
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

        views_map[f"Round {round_item['round_number']}"] = round_view

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

    navigation_menu = ft.Column(
        controls=[],
        alignment=ft.MainAxisAlignment.START,
        spacing=15,
        scroll=ft.ScrollMode.HIDDEN
    )

    for i, title in enumerate(views_map.keys()):
        navigation_menu.controls.append(
            ft.TextButton(
                content=ft.Text(
                    title, 
                    size=24, 
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.ON_SURFACE,
                ),
                on_click=handle_menu_click,
                style=ft.ButtonStyle(padding=0)
            )
        )

    main_view = ft.Row(
        vertical_alignment=ft.CrossAxisAlignment.START,
        controls=[
            ft.Container(
                content=navigation_menu,
                width=180,
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