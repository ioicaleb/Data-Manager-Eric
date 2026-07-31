import flet as ft
from data_processing.search_processor import search_songs, find_round_by_song_id

def generate_songs_tab(page: ft.Page):
    """
    Renders an on-demand keyword search dashboard canvas utilizing 
    high-speed dictionary indexes loaded into container memory.
    """
    content_height = max(400, (page.height or 900) - 260)

    results_list = ft.Column(
        spacing=15,
        height=content_height,
        controls=[],
        scroll=ft.ScrollMode.AUTO
    )

    def search_song(e=None):
        keyword = search_input.value.strip().lower() if search_input.value else ""
        results_list.controls.clear()

        if not keyword or keyword.__len__() < 3:
            status_text.value = "Enter a song name, artist, or album to search."
            page.update()
            return
        
        status_text.value = f"Searching for '{keyword}'..."
        page.update()

        titles_list = set()
        unique_results = []

        songs_data = search_songs(keyword) or []
        max_results = 100
        songs_data = songs_data[:max_results]

        for song in songs_data:
            title = song.get("name")
            if title not in titles_list:
                titles_list.add(title)
                unique_results.append(song)

        songs_data = unique_results

        if len(songs_data) == 0:
            status_text.value = f"No matches found for '{search_input.value}'."
        else:
            status_text.value = f"Found {len(songs_data)} matching song{'s' if len(songs_data) > 1 else ''}:"

        for song in songs_data:
            title = song.get("name", "Unknown Title")
            artist = song.get("artist", "Unknown Artist")
            album = song.get("album", "Unknown Album")
            player = song.get("player_name", "Unknown")
            votes = song.get("votes", 0)
            
            round_item = find_round_by_song_id(song.get("id"))
            if round_item:
                round_number = round_item.get("round_number", "?")
                round_title = round_item.get("title", "Unknown Round")
            else:
                round_number = "?"
                round_title = "Unassigned Round"

            song_card = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.AUDIOTRACK, size=24, color=ft.Colors.BLUE_400),
                                ft.Text(title, size=22, weight=ft.FontWeight.BOLD)
                            ],
                            spacing=10
                        ),
                        
                        ft.ResponsiveRow(
                            spacing=15,
                            controls=[
                                ft.Column([ft.Row([ft.Icon(ft.Icons.MIC, size=20, color="purple200"), ft.Text(f"Artist: {artist}", size=15)])], col={"lg": 3, "md": 6, "sm": 12}),
                                ft.Column([ft.Row([ft.Icon(ft.Icons.ALBUM, size=20, color="purple200"), ft.Text(f"Album: {album}", size=15)])], col={"lg": 3, "md": 6, "sm": 12}),
                                ft.Column([ft.Row([ft.Icon(ft.Icons.PERSON, size=20, color="amber200"), ft.Text(f"Submitted By: {player}", size=15)])], col={"lg": 3, "md": 6, "sm": 12}),
                                ft.Column([ft.Row([ft.Icon(ft.Icons.PLAYLIST_PLAY, size=20, color="greenAccent200"), ft.Text(f"Round {round_number}: {round_title}", size=15)])], col={"lg": 3, "md": 6, "sm": 12}),
                            ]
                        ),
                        
                        ft.Row(
                            controls=[    
                                ft.Icon(ft.Icons.THUMB_UP_ALT_ROUNDED, size=20, color="amber"),
                                ft.Text(f"Accumulated {votes} Points Total", size=15, weight=ft.FontWeight.W_600)
                            ],
                            spacing=8
                        )
                    ],
                    spacing=15
                ),
                padding=ft.Padding(15, 15, 15, 15),
                bgcolor=ft.Colors.SURFACE_CONTAINER_LOW if page.theme_mode == ft.ThemeMode.DARK else ft.Colors.SURFACE_CONTAINER_HIGH,
                border_radius=8,
                border=ft.BorderSide(width=1, color=ft.Colors.GREY_800)
            )
            results_list.controls.append(song_card)
        page.update()

    search_input = ft.TextField(
        label="Search songs, artists or albums",
        prefix_icon=ft.Icons.SEARCH,
        on_change=search_song,
        on_submit=search_song,
        expand=True
    )

    clear_button = ft.IconButton(
        icon=ft.Icons.CLEAR,
        tooltip="Clear search",
        on_click=lambda _: (setattr(search_input, "value", ""), results_list.controls.clear(), setattr(status_text, "value", "Enter a song name, artist, or album to search."), page.update())
    )

    status_text = ft.Text("Enter a song name, artist, or album to search.", size=16, color="grey400")

    song_check_container = ft.Container(
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[search_input, clear_button],
                    alignment=ft.MainAxisAlignment.START,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER
                ),
                status_text,
                ft.Divider(height=10, thickness=1, color=ft.Colors.GREY_800),
                ft.Container(content=results_list, expand=True)
            ],
            expand=True,
            spacing=15
        ),
        padding=ft.Padding(20, 20, 20, 20),
        expand=True
    )
        
    return song_check_container