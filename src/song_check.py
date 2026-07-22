import flet as ft
from DataProcessing.search_processor import search_songs, find_round_by_song_id

search_task = None

def generate_songs_tab(page: ft.Page):
    results_list = ft.Column(
        spacing=10,
        expand=True,
        controls=[],
        scroll= ft.ScrollMode.HIDDEN
    )

    def search_song(e = None):
        global search_task
 
        keyword = search_input.value.strip().lower()
        results_list.controls.clear()

        if not keyword:
            status_text.value = "Enter a song name, artist, or album to search."
            page.update()
            return
        
        status_text.value = f"Searching for '{keyword}'..."
        page.update()

        titles_list = set()
        unique_results = []

        songs_data = search_songs(keyword)
        max_results = 100
        songs_data = songs_data[:max_results]

        for song in songs_data:
            title = song.get("name")
            if title not in titles_list:
                titles_list.add(title)
                unique_results.append(song)

        songs_data = unique_results

        if len(songs_data) == 0:
            status_text.value = f"No matches found for {search_input.value}."
        else:
            status_text.value = f"Found {len(songs_data)} matching song{'s' if len(songs_data) > 1 else ''}:"

        for song in songs_data:
            title = song.get("name")
            artist = song.get("artist")
            album = song.get("album")
            player = song.get("player_name")
            votes = song.get("votes")
            round_item = find_round_by_song_id(song.get("id"))
            round_id = round_item.get("round_number")
            round_title = round_item.get("title")

            song_card = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.AUDIOTRACK, size=22, color=ft.Colors.BLUE_400),
                                ft.Text(title, size=24, weight=ft.FontWeight.W_500)
                            ]
                        ),
                        ft.Row(
                            controls=[
                                ft.Row(
                                    controls= [
                                        ft.Icon(ft.Icons.MIC, size = 22),
                                        ft.Text(f"Artist: {artist}", size = 18)
                                    ]
                                ),
                                ft.Row(
                                    controls = [
                                        ft.Icon(ft.Icons.ALBUM, size = 22),
                                        ft.Text(f"Album: {album}", size=18)
                                    ]
                                ),
                                ft.Row(
                                    controls= [
                                        ft.Icon(ft.Icons.LOGIN_OUTLINED, size = 22),
                                        ft.Text(f"Submitted By: {player}", size = 18)
                                    ]
                                ),
                                ft.Row(
                                    controls = [
                                        ft.Icon(ft.Icons.PLAYLIST_PLAY, size = 22),
                                        ft.Text(f"For Round {round_id}: {round_title}", size=18)
                                    ]
                                )
                            ],
                        ),
                        ft.Row(
                            controls = [    
                                ft.Row(
                                    controls = [
                                        ft.Icon(ft.Icons.THUMB_UP_ALT_ROUNDED, size = 22),
                                        ft.Text(f"It got {votes} points", size=18)
                                    ]
                                )
                            ],
                            spacing = 20
                        )
                    ],
                    spacing = 24
                ),
                padding = ft.Padding(15, 15, 15, 15),
                bgcolor = ft.Colors.SURFACE_CONTAINER_LOW if page.theme_mode == ft.ThemeMode.DARK else ft.Colors.SURFACE_CONTAINER_HIGH,
                border_radius = 8,
                border = ft.BorderSide(width = 1, color=ft.Colors.GREY_800)
            )
            results_list.controls.append(song_card)
        page.update()

    search_input = ft.TextField(
        label = "Search songs, artists or albums",
        prefix_icon= ft.Icons.SEARCH,
        on_change = search_song,
        on_submit = search_song,
        expand = True
    )

    clear_button = ft.IconButton(
        icon = ft.Icons.CLEAR,
        tooltip = "Clear search",
        on_click = lambda _: (setattr(search_input, "value", ""), search_song(None))
    )

    status_text = ft.Text("Enter a song name, artist, or album to search.", size = 18)

    song_check_container = ft.Container(
        content = ft.Column(
            controls = [
                ft.Row(
                    controls=[
                        search_input,
                        clear_button
                    ],
                    alignment = ft.MainAxisAlignment.START,
                    vertical_alignment = ft.CrossAxisAlignment.CENTER
                ),
                status_text,
                ft.Divider(height = 10, thickness = 1, color = ft.Colors.GREY_800),
                ft.Container(content = results_list, expand = True)
            ],
            expand = True,
            spacing= 15
        ),
        padding=ft.Padding(20, 20, 20, 20),
        expand= True
    )
        
    return song_check_container