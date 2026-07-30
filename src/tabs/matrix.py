import flet as ft
from data_processing.search_processor import get_players
from data_processing.data_processor import prepare_master_matrix

def generate_matrix_tab(page: ft.Page):
    is_mobile = (page.width or 1200) < 700
    COLUMN_WIDTH = 56 if is_mobile else 80
    DATA_CELL_WIDTH = COLUMN_WIDTH + (12 if is_mobile else 20)

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

    vertical_scroll_column = ft.Column(
        expand=True,
        spacing=10,
        scroll=ft.ScrollMode.HIDDEN,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER 
    )

    scrollable_horizontal_track = ft.Row(
        controls=[matrix_table],  
        scroll=ft.ScrollMode.HIDDEN,
        expand=True,
        alignment=ft.MainAxisAlignment.CENTER 
    )

    vertical_scroll_column.controls.append(scrollable_horizontal_track)

    matrix_container = ft.Container(
        content=ft.Row(
            controls=[vertical_scroll_column],
            alignment=ft.MainAxisAlignment.CENTER
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
                if name == "[Left the league]" or name == "":
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
                if isinstance(player, dict) and player.get("name") and player.get("name") != "[Left the league]":
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
        
        if isinstance(matrix_data, list):
            for row_payload in matrix_data:                
                new_row = ft.DataRow(cells=[])
                
                if isinstance(row_payload, list) and len(row_payload) > 0:
                    row_player_name = str(row_payload[0])
                    if row_player_name != "[Left the league]":
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
                        
                        for col_index, name in enumerate(player_keys):
                            payload_score_index = col_index + 1
                            
                            score = row_payload[payload_score_index] if payload_score_index < len(row_payload) else "-"
                            
                            if row_player_name.strip().lower() == str(name).strip().lower():
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