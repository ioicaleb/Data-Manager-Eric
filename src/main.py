import asyncio
import inspect
import os
from DataCollection.data_collector import collect_data, new_round_check, analyze_stats
from DataCollection.json_manager import *
from DataProcessing.data_processor import *
from player_stats import generate_profile_tab
from matrix import generate_matrix_tab
from standings import generate_standings_tab
from rounds import generate_rounds_tab
from song_check import generate_songs_tab
import flet as ft

def main(page: ft.Page, start_tab_index=0): 
    page.title = "Eric the Data Manager"
    page.theme_mode = ft.ThemeMode.DARK
    page.horizontal_alignment = ft.CrossAxisAlignment.START
    page.vertical_alignment = ft.MainAxisAlignment.START
    
    def toggle_theme(e):
        if page.theme_mode == ft.ThemeMode.DARK:
            page.theme_mode = ft.ThemeMode.LIGHT
            theme_switch.icon = ft.Icons.BRIGHTNESS_7
        else:
            page.theme_mode = ft.ThemeMode.DARK
            theme_switch.icon = ft.Icons.BRIGHTNESS_4
        page.update()
    
    theme_switch = ft.IconButton(
        icon=ft.Icons.BRIGHTNESS_4,
        on_click=toggle_theme,
        tooltip="Toggle theme"
    )

    def return_callback(page_obj, index):
        main(page_obj, start_tab_index=index)
    
    standings_container = generate_standings_tab(page)
    matrix_container = generate_matrix_tab(page)
    profiles_container = generate_profile_tab(page, return_callback)
    rounds_container = generate_rounds_tab(page)
    songs_container = generate_songs_tab(page)

    tab_view = ft.Column(
        expand=True,
        controls=[
            ft.TabBar(
                tabs=[
                    ft.Tab(label="Standings", icon=ft.Icons.LEADERBOARD),
                    ft.Tab(label="Matrix", icon=ft.Icons.GRID_ON),
                    ft.Tab(label="Player Stats", icon=ft.Icons.PERSON),
                    ft.Tab(label="Round Stats", icon=ft.Icons.QUEUE_MUSIC),
                    ft.Tab(label="Check Song", icon=ft.Icons.MUSIC_NOTE)
                ]
            ),
            ft.TabBarView(
                expand=True,
                controls=[
                    standings_container,
                    matrix_container,
                    profiles_container,
                    rounds_container,
                    songs_container
                ]
            )
        ]
    )

    page.add(
        ft.Column(
            expand=True,
            controls=[
                ft.Container(
                    margin=ft.Margin(0, 10, 0, 20), 
                    content=ft.Stack(
                        height=60,
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text("Eric the Data Manager", size=42, weight=ft.FontWeight.BOLD)
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                            ),
                            ft.Container(
                                content=theme_switch,
                                right=10,
                                top=0,
                            )
                        ],
                    ),
                ),     
                tab_view
            ],
        )
    )
    page.update()

def show_loading_page(page: ft.Page):
    """Show a loading page with progress visualization during data collection"""
    loading_text = ft.Text("Eric Is Getting the Data", size=42, weight=ft.FontWeight.BOLD)
    progress_bar = ft.ProgressBar(width=400, color="blue", value=0.1)
    status_text = ft.Text("Initializing...", size=32)
    loading_spinner = ft.ProgressRing(visible=False)
    
    loading_layout = ft.Column(
        controls=[
            loading_text,
            ft.Divider(),
            ft.Text("Collecting and Processing Data...", size=32, weight=ft.FontWeight.BOLD),
            ft.Container(content=progress_bar, padding=20),
            status_text,
            ft.Text("Please wait...", size=24, color=ft.Colors.GREY_500),
            loading_spinner
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        expand=True
    )
    
    page.add(loading_layout)
    return progress_bar, status_text, loading_spinner

async def loading(page: ft.Page):
    page.title = "Eric the Data Manager"
    page.theme_mode = ft.ThemeMode.DARK
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    
    progress_bar, status_text, loading_spinner = show_loading_page(page)
    page.update() 
    
    async def background_crawler_pipeline():
        try:
            await asyncio.sleep(0.3)
            
            progress_bar.value = 0.0
            status_text.value = "Checking for new round..."
            page.update() 
            
            if not check_date() and read_json("rounds"):
                progress_bar.value = 1.0
                status_text.value = "Up to Date"
                page.update()
                
                await asyncio.sleep(0.8)
                page.controls.clear()
                
                if inspect.iscoroutinefunction(main):
                    await main(page)
                else:
                    main(page)
                page.update()
                return
            
            progress_bar.value = 0.2
            status_text.value = "Starting data collection..."
            page.update() 
            
            await asyncio.to_thread(collect_data)
            
            progress_bar.value = 0.4
            status_text.value = "Processing collected data..."
            page.update()

            await asyncio.to_thread(new_round_check)
            
            progress_bar.value = 0.8
            status_text.value = "Loading data into UI..."
            page.update()

            await asyncio.to_thread(analyze_stats)

            save_app_data()
            page.controls.clear()
            
            if inspect.iscoroutinefunction(main):
                await main(page)
            else:
                main(page)
                
            page.update()
            
        except Exception as e:
            print(f"Pipeline failure: {e}")
            page.controls.clear()
            page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
            page.vertical_alignment = ft.MainAxisAlignment.CENTER
            page.add(
                ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Icon(ft.Icons.ERROR_OUTLINE, color=ft.Colors.RED, size=50),
                        ft.Text(f"Error during collection pipeline:\n{str(e)}", size=18, color=ft.Colors.RED, text_align=ft.TextAlign.CENTER)
                    ]
                )
            )
            page.update()

    page.run_task(background_crawler_pipeline)


if __name__ == "__main__":
    port_to_use = int(os.environ.get("PORT", 8502)) 
    
    ft.run(
        loading, 
        view=ft.AppView.WEB_BROWSER,  
        port=port_to_use,                     
        host="0.0.0.0",
        assets_dir="assets"             
    )