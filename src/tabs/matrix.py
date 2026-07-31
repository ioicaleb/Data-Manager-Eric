import flet as ft
from data_processing.search_processor import get_players
from data_processing.data_processor import prepare_master_matrix

def generate_matrix_tab(page: ft.Page):
    is_mobile = (page.width or 1200) < 700
    COLUMN_WIDTH = 56 if is_mobile else 80
    DATA_CELL_WIDTH = COLUMN_WIDTH + (12 if is_mobile else 20)
    content_height = max(400, (page.height or 900) - 220)

    matrix_table = ft.DataTable(
        columns=[
            ft.DataColumn(
                label=ft.Container(
                    content=ft.Text("", weight=ft.FontWeight.BOLD),
                    width=COLUMN_WIDTH + 10,
                    alignment=ft.Alignment.CENTER
                )
            )
        ],
        rows=[],
        heading_row_color=ft.Colors.SURFACE_CONTAINER_HIGHEST,
        vertical_lines=ft.BorderSide(width=1, color=ft.Colors.GREY_800),
        column_spacing=0,
        data_row_min_height=52,
        data_row_max_height=52,
        heading_row_height=52
    )  

    content_width = max(400, (page.width or 1200) - 40)

    vertical_scroll_column = ft.Column(
        height=content_height,
        width=content_width,
        spacing=10,
        scroll=ft.ScrollMode.HIDDEN,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER 
    )

    scrollable_horizontal_track = ft.Row(
        controls=[matrix_table],  
        scroll=ft.ScrollMode.HIDDEN,
        width=content_width,
        alignment=ft.MainAxisAlignment.CENTER 
    )

    vertical_scroll_column.controls.append(scrollable_horizontal_track)

    matrix_container = ft.Container(
        content=ft.Row(
            controls=[vertical_scroll_column],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.START
        ),
        expand=True,
        padding=10
    )

    def hydrate_live_matrix_grid():
        """
        Dynamically extracts active data parameters from memory.
        Clears table matrices on-demand, preventing data leak collisions.
        """
        matrix_table.columns = [matrix_table.columns[0]]
        matrix_table.rows.clear()
        
        player_keys = []
        players_data = get_players() or []

        if isinstance(players_data, dict):
            for name in players_data.keys():
                if name == "[Left the league]":
                    continue
                player_keys.append(name)
                matrix_table.columns.append(
                    ft.DataColumn(
                        ft.Container(
                            width=COLUMN_WIDTH + 10,
                            alignment=ft.Alignment.CENTER,
                            content=ft.Text(name, size=14 if is_mobile else 18)
                        )
                    )
                )
        elif isinstance(players_data, list):
            for player in players_data:
                if isinstance(player, dict) and player.get("name") != "[Left the league]":
                    name = player.get("name", "Unknown")
                    player_keys.append(name)
                    matrix_table.columns.append(
                        ft.DataColumn(
                            ft.Container(
                                width=COLUMN_WIDTH + 10,
                                alignment=ft.Alignment.CENTER,
                                content=ft.Text(name, size=14 if is_mobile else 18),
                            ),
                        )
                    )

        matrix_data = prepare_master_matrix() or []

        for row_payload in matrix_data:
            if not isinstance(row_payload, dict):
                continue

            row_player_name = str(row_payload.get("player", ""))
            row_votes = row_payload.get("votes", {}) or {}
            if not row_player_name or row_player_name == "[Left the league]":
                continue

            new_row = ft.DataRow(cells=[])
            new_row.cells.append(
                ft.DataCell(
                    ft.Container(
                        content=ft.Text(row_player_name, size=13 if is_mobile else 16, weight=ft.FontWeight.BOLD),
                        width=DATA_CELL_WIDTH,
                        height=48,
                        alignment=ft.Alignment.CENTER
                    )
                )
            )
            votes_lookup = {str(k): v for k, v in row_votes.items()}

            for name in player_keys:
                if row_player_name == str(name):
                    new_row.cells.append(
                        ft.DataCell(
                            ft.Container(
                                width=DATA_CELL_WIDTH,
                                height=48,
                                bgcolor=ft.Colors.BLACK,
                                alignment=ft.Alignment.CENTER
                            )
                        )
                    )
                else:
                    score = votes_lookup.get(str(name), "-")
                    new_row.cells.append(
                        ft.DataCell(
                            ft.Container(
                                content=ft.Text(str(score), size=13 if is_mobile else 16, text_align=ft.TextAlign.CENTER),
                                width=DATA_CELL_WIDTH,
                                height=48,
                                alignment=ft.Alignment.CENTER
                            )
                        )
                    )

            matrix_table.rows.append(new_row)

    hydrate_live_matrix_grid()
    return matrix_container