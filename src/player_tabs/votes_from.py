import flet as ft

def generate_votes_from(player_stats_data, player_name):
    """
    Renders an in-memory sub-tab list illustrating the total points
    the selected player has received from each of their league opponents.
    """
    raw_votes_from = player_stats_data.get("votes_from_data") or {}
    
    
    if isinstance(raw_votes_from, dict):
        votes_from_data = sorted(raw_votes_from.items(), key=lambda x: x[1], reverse=True)
    elif isinstance(raw_votes_from, list):
        
        if len(raw_votes_from) > 0 and isinstance(raw_votes_from[0], (list, tuple)):
            votes_from_data = sorted(raw_votes_from, key=lambda x: x[1], reverse=True)
        else:
            votes_from_data = []
    else:
        votes_from_data = []

    
    votes_from_list = ft.Container(
        content=ft.Column(
            controls=[], 
            scroll=ft.ScrollMode.HIDDEN,
            spacing=10
        ),
        border_radius=10,
        height=600,
        expand=True
    )

    for voter_name, vote_count in votes_from_data:
        if str(voter_name).lower() != str(player_name).lower():
            votes_from_list.content.controls.append(
                ft.Card(
                    content=ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Row([
                                    ft.Icon(ft.Icons.FAVORITE, color="red400", size=24),
                                    ft.Text(f"{voter_name}", size=24, weight=ft.FontWeight.W_500)
                                ], spacing=10),
                                ft.Text(f"{vote_count} pts total", size=22, weight=ft.FontWeight.BOLD, color="amber200")
                            ],
                            width = 300,
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                        padding = 20
                    ),
                    margin = ft.Margin(left = 60)
                )
            )

    votes_from = ft.Container(
        content=votes_from_list,
        expand=True,
        visible=False
    )

    return votes_from