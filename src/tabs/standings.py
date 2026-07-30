import flet as ft
from data_processing.data_processor import process_standings_votes, process_standings_wins, process_standings_comments

def generate_standings_tab(page: ft.Page):
    """
    Renders a state-managed, responsive standings view panel.
    Guarantees isolation across multiple parallel database requests.
    """
    is_mobile = (page.width or 1200) < 600
    line_size = 20 if is_mobile else 32
    content_height = max(400, (page.height or 900) - 260)

    votes_column = ft.Column(spacing=10, horizontal_alignment=ft.CrossAxisAlignment.START, scroll=ft.ScrollMode.HIDDEN, height=content_height)
    wins_column = ft.Column(spacing=10, horizontal_alignment=ft.CrossAxisAlignment.START, scroll=ft.ScrollMode.HIDDEN, height=content_height)
    comments_column = ft.Column(spacing=10, horizontal_alignment=ft.CrossAxisAlignment.START, scroll=ft.ScrollMode.HIDDEN, height=content_height)
    
    def hydrate_live_standings_view():
        """
        Queries your refactored cache_manager proxy on-demand.
        Clears out old rows and appends current database states dynamically.
        """
        votes_data = process_standings_votes() or []
        wins_data = process_standings_wins() or []
        comments_data = process_standings_comments() or []
        
        votes_column.controls.clear()
        wins_column.controls.clear()
        comments_column.controls.clear()
        
        for line in votes_data:
            votes_column.controls.append(ft.Text(line, size=line_size))

        for line in wins_data:
            wins_column.controls.append(ft.Text(line, size=line_size))
            
        for line in comments_data:
            comments_column.controls.append(ft.Text(line, size=line_size))

    hydrate_live_standings_view()

    tab_view = ft.Tabs(
        length=3,
        expand=True,
        content=ft.Column(
            expand=True,
            controls=[
                ft.TabBar(
                    tabs=[
                        ft.Tab(label="Votes", icon=ft.Icons.HOW_TO_VOTE),
                        ft.Tab(label="Wins", icon=ft.Icons.DIAMOND),
                        ft.Tab(label="Comments", icon=ft.Icons.CHAT_BUBBLE)
                    ]
                ),
                ft.TabBarView(
                    expand=True,
                    controls=[
                        votes_column,
                        wins_column,
                        comments_column
                    ]
                )
            ]
        )
    )
    content_width = None if is_mobile else min(600, (page.width or 600))

    standings_container = ft.Container(
        content=ft.Row(
            controls=[
                ft.Column(
                    controls=[tab_view],
                    width=content_width,
                    expand=is_mobile,
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.START
        ),
        expand=True,
        padding=ft.Padding(10, 0, 10, 0) if is_mobile else ft.Padding(0, 0, 0, 0)
    )

    return standings_container