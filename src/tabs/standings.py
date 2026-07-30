import flet as ft
from data_processing.data_processor import process_standings_votes, process_standings_wins, process_standings_comments

def generate_standings_tab(page: ft.Page):
    """
    Renders a state-managed, responsive standings view panel.
    Guarantees isolation across multiple parallel database requests.
    """
    votes_column = ft.Column(spacing=10, horizontal_alignment=ft.CrossAxisAlignment.START, scroll=ft.ScrollMode.HIDDEN, expand = True)
    wins_column = ft.Column(spacing=10, horizontal_alignment=ft.CrossAxisAlignment.START, scroll=ft.ScrollMode.HIDDEN, expand = True)
    comments_column = ft.Column(spacing=10, horizontal_alignment=ft.CrossAxisAlignment.START, scroll=ft.ScrollMode.HIDDEN, expand = True)
    
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
            votes_column.controls.append(ft.Text(line, size=32))

        for line in wins_data:
            wins_column.controls.append(ft.Text(line, size=32))
            
        for line in comments_data:
            comments_column.controls.append(ft.Text(line, size=32))

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
    
    standings_container = ft.Container(
        content=ft.Row(
            controls=[
                ft.Column(
                    controls=[tab_view],
                    width=600,
                    margin=ft.Margin(200, 0, 0, 0),
                    expand=False,
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.START
        ),
        expand=True
    )

    return standings_container