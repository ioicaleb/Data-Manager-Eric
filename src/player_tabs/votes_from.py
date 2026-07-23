import flet as ft

def generate_votes_from(player_stats_data, player_name):
    votes_from_data = player_stats_data.get("votes_from_data") or {}
    votes_from_data = sorted(votes_from_data.items(), key=lambda x: x[1], reverse=True)

    votes_from_list = ft.Container(
        content = ft.Column(
            controls = [], 
            scroll= ft.ScrollMode.HIDDEN,
        ),
        border_radius=10,
        height= 600,
        expand = True
    )

    for voter_name, vote_count in votes_from_data:
        if voter_name != player_name:
            votes_from_list.content.controls.append(
                ft.Row(
                    controls=[
                        ft.Text(f"{voter_name}", size=28, weight= ft.FontWeight.W_500),
                        ft.Text(f": {vote_count}", size=24)
                    ]
                )
            )

    votes_from = ft.Container(
        content= votes_from_list,
        expand=True,
        visible=False
    )

    return votes_from