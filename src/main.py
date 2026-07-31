import base64, httpx, os, psycopg2, json, asyncio, sys, hashlib
from psycopg2.extras import RealDictCursor
import flet as ft
import flet.fastapi as flet_fastapi
from fastapi import FastAPI

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from tabs.profile_stats import generate_profile_tab
from tabs.matrix import generate_matrix_tab
from tabs.standings import generate_standings_tab
from tabs.rounds import generate_rounds_tab
from tabs.song_check import generate_songs_tab

from data_processing.cache_manager import initialize_memory_cache
from data_processing.search_processor import clear_search_processor_globals, init_search_cache
from data_processing.cache_builder import build_static_dashboard_cache
from data_collection.data_collector import run_pipeline_migration

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is missing from your local session.")

conn = psycopg2.connect(DATABASE_URL, sslmode="require")
cur = conn.cursor()

create_table_query = """
CREATE TABLE IF NOT EXISTS music_leagues (
    league_id VARCHAR(255) PRIMARY KEY,
    admin_password_hash VARCHAR(255),
    browser_type VARCHAR(50),
    scraped_data JSONB
);
"""

print("Initializing music_leagues table structure...")
cur.execute(create_table_query)
conn.commit()
cur.close()
conn.close()
print("Database successfully generated!")

def get_league_data_from_postgres(league_id: str) -> dict:
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        print("Warning: DATABASE_URL environment variable is missing.")
        return {}
    conn = psycopg2.connect(DATABASE_URL, sslmode="require")
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT scraped_data FROM music_leagues WHERE league_id = %s;", (league_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row or not row["scraped_data"]:
        return {}
    return row["scraped_data"]

def save_league_data_to_postgres(league_id: str, secret_pwd_hash: str, payload: dict, browser: str):
    DATABASE_URL = os.getenv("DATABASE_URL")
    conn = psycopg2.connect(DATABASE_URL, sslmode="require")
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM music_leagues WHERE league_id = %s;", (league_id,))
    exists = cur.fetchone()
    if exists:
        cur.execute(
            "UPDATE music_leagues SET scraped_data = %s, browser_type = %s WHERE league_id = %s;",
            (json.dumps(payload), browser, league_id)
        )
    else:
        cur.execute(
            "INSERT INTO music_leagues (league_id, admin_password_hash, browser_type, scraped_data) VALUES (%s, %s, %s, %s);",
            (league_id, secret_pwd_hash, browser, json.dumps(payload))
        )
    conn.commit()
    cur.close()
    conn.close()

def verify_admin_password_hash(league_id: str, submitted_password_hash: str) -> bool:
    DATABASE_URL = os.getenv("DATABASE_URL")
    conn = psycopg2.connect(DATABASE_URL, sslmode="require")
    cur = conn.cursor()
    cur.execute("SELECT admin_password_hash FROM music_leagues WHERE league_id = %s;", (league_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row and row[0] != submitted_password_hash:
        return False
    return True

async def main_dashboard(page: ft.Page, start_tab_index=0, progress_callback=None):
    """Your original visual layout manager. Renders analytics from active memory cache.

    This is async (must be awaited) so it can await generate_profile_tab and
    actually yield to the event loop between progress updates — see the
    docstring on generate_profile_tab for why that matters.

    progress_callback, if provided, is called as (fraction: float, message: str)
    while the dashboard's tabs — especially player profiles, the slowest one —
    are being built, so a loading screen can stay up and show what's happening.
    """
    async def _report(fraction: float, message: str):
        if progress_callback:
            progress_callback(fraction, message)
        await asyncio.sleep(0)

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

    async def return_callback(page_obj):
        page_obj.controls.clear()
        await main_dashboard(page_obj, start_tab_index=2)
    
    await _report(0.05, "Building standings...")
    standings_container = generate_standings_tab(page)

    await _report(0.15, "Building vote matrix...")
    matrix_container = generate_matrix_tab(page)

    try:
        def _profile_progress(fraction: float, message: str):
            progress_callback(0.20 + fraction * 0.60, message)

        profiles_container = await generate_profile_tab(
            page,
            return_callback,
            progress_callback=_profile_progress if progress_callback else None
        )
        if profiles_container is None:
            raise ValueError("Profile tab function returned None value string configuration.")
    except Exception as e:
        print(f"Warning: profiles_container failed to initialize: {e}")
        profiles_container = ft.Container(
            content=ft.Text(f"Profiles tab initialization error: {str(e)}"),
            padding=20
        )

    await _report(0.85, "Building round stats...")
    rounds_container = generate_rounds_tab(page)

    await _report(0.93, "Building song checker...")
    songs_container = generate_songs_tab(page)

    await _report(0.98, "Assembling...")

    dashboard_is_mobile = (page.width or 1200) < 700

    tab_view = ft.Tabs(
        length=5,
        selected_index=start_tab_index,
        expand=False,
        content=ft.Column(
            expand=True,
            controls=[
                ft.TabBar(
                    scrollable=dashboard_is_mobile,
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
    )

    await _report(1.0, "Done! Launching...")
    page.controls.clear()
    page.add(
        ft.Column(
            expand=True,
            controls=[
                ft.Container(
                    margin=ft.Margin(0, 10, 0, 20), 
                    content=ft.Stack(
                        height=70,
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text(
                                        "🎵 Eric the Data Manager" if not dashboard_is_mobile else "🎵 Eric",
                                        size=28 if dashboard_is_mobile else 50,
                                        weight=ft.FontWeight.BOLD,
                                        text_align=ft.TextAlign.CENTER
                                    )
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
    """Renders a visual pipeline loading bar layout on the screen."""
    page.controls.clear()
    
    loading_text = ft.Text("Eric is Processing Your League", size=36, weight=ft.FontWeight.BOLD)
    
    progress_bar = ft.ProgressBar(width=min(400, (page.width or 400) - 40), color="purple", value=0.0)
    status_text = ft.Text("Initializing secure runtime containers...", size=24, color="grey400")
    loading_spinner = ft.ProgressRing(width=20, stroke_width=2, color="purple")
    
    loading_layout = ft.Column(
        controls=[
            loading_text,
            ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
            ft.Container(content=progress_bar, border_radius=10),
            ft.Row(
                controls=[loading_spinner, status_text], 
                spacing=15, 
                alignment=ft.MainAxisAlignment.CENTER
            ),
            ft.Text("Please do not close this browser window.", size=18, color="grey600"),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        expand=True
    )
    
    page.add(loading_layout)
    page.update()
    
    return progress_bar, status_text

async def show_username_mapping_wizard(page: ft.Page, payload: dict, league_id: str, pwd_hash: str):
    """
    Renders an interactive administrative onboarding panel to map 
    scraped system usernames directly to clean visual profile names.

    Blocks until the user clicks Save or Skip — the caller must await
    this. Without blocking, whatever code runs immediately after showing
    the wizard would race ahead and repaint the page before the user
    could finish, using stale data that hasn't had the mapping applied.
    """
    wizard_done = asyncio.Event()
    page.title = "Username Wizard"
    
    existing_map = payload.get("username_mapping") or {}
    scraped_users = list(payload.get("avatars", {}).keys())
    
    if "[Left the league]" in scraped_users:
        scraped_users.remove("[Left the league]")

    mapping_rows = ft.Column(spacing=15, scroll=ft.ScrollMode.HIDDEN, expand=True)
    text_fields_registry = {}

    def build_mapping_row(username: str, prefill_value: str = ""):
        row_is_mobile = (page.width or 1200) < 700
        input_field = ft.TextField(
            label="Preferred Display Name",
            value=prefill_value or username,
            width=None if row_is_mobile else 280,
            expand=row_is_mobile,
            hint_text="e.g., Eric S."
        )
        text_fields_registry[username] = input_field
        
        if row_is_mobile:
            content = ft.Column(
                spacing=8,
                controls=[
                    ft.Row([
                        ft.Icon(ft.Icons.PERSON_OUTLINE, color="purple"),
                        ft.Text(username, size=18, weight=ft.FontWeight.BOLD, expand=True)
                    ]),
                    input_field
                ]
            )
        else:
            content = ft.Row(
                controls= [
                    ft.Icon(ft.Icons.PERSON_OUTLINE, color="purple"),
                    ft.Text(username, size=20, weight=ft.FontWeight.BOLD, width=200),
                    ft.Icon(ft.Icons.ARROW_FORWARD, color="grey600"),
                    input_field
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            )
        return ft.Container(
            padding=10,
            border_radius=8,
            bgcolor=ft.Colors.GREY_900 if page.theme_mode == ft.ThemeMode.DARK else ft.Colors.GREY_100,
            content=content
        )

    for user in scraped_users:
        build_value = existing_map.get(user, "")
        mapping_rows.controls.append(build_mapping_row(user, prefill_value=build_value))

    extra_players_count = 0
    def handle_add_custom_player(e):
        nonlocal extra_players_count
        extra_players_count += 1
        placeholder_key = f"Custom_Unset_Player_{extra_players_count}"
        
        new_row = build_mapping_row(placeholder_key, prefill_value=f"New Player {extra_players_count}")
        mapping_rows.controls.append(new_row)
        page.update()

    async def handle_save_and_sync(e):
        compiled_username_map = {}
        new_players_list = payload.get("players") or []

        for username_key, text_control in text_fields_registry.items():
            clean_display_name = text_control.value.strip()
            if not clean_display_name:
                clean_display_name = username_key

            compiled_username_map[username_key] = clean_display_name

            player_exists = any(p.get("name") == clean_display_name for p in new_players_list)
            if not player_exists:
                new_players_list.append({
                    "name": clean_display_name,
                    "position": "#?",
                    "votes_to": 0,
                    "is_manual_entry": "Custom_Unset" in username_key
                })
        remapped_away_names = {
            raw for raw, mapped in compiled_username_map.items() if raw != mapped
        }
        new_players_list = [
            p for p in new_players_list
            if p.get("name") not in remapped_away_names
        ]

        payload["username_mapping"] = compiled_username_map
        payload["players"] = new_players_list
        existing_songs = payload.get("songs") or []
        for song in existing_songs:
            if not isinstance(song, dict):
                continue
            raw_submitter = song.get("player_name")
            if raw_submitter in compiled_username_map:
                song["player_name"] = compiled_username_map[raw_submitter]
            for voter in song.get("voters", []) or []:
                if not isinstance(voter, dict):
                    continue
                raw_voter = voter.get("name")
                if raw_voter in compiled_username_map:
                    voter["name"] = compiled_username_map[raw_voter]
        payload["songs"] = existing_songs

        initialize_memory_cache(payload)
        build_static_dashboard_cache(payload)
        init_search_cache()

        save_league_data_to_postgres(
            league_id=league_id,
            secret_pwd_hash=pwd_hash,
            payload=payload,
            browser=payload.get("browser_type", "chromium")
        )

        page.controls.clear()
        page.horizontal_alignment = ft.CrossAxisAlignment.START
        page.vertical_alignment = ft.MainAxisAlignment.START
        await main_dashboard(page)
        wizard_done.set()

    async def handle_skip_wizards(e):
        if not payload.get("username_mapping"):
            payload["username_mapping"] = {u: u for u in scraped_users}
            
        initialize_memory_cache(payload)
        build_static_dashboard_cache(payload)
        init_search_cache()
        
        page.controls.clear()
        page.horizontal_alignment = ft.CrossAxisAlignment.START
        page.vertical_alignment = ft.MainAxisAlignment.START
        await main_dashboard(page)
        wizard_done.set()

    wizard_is_mobile = (page.width or 1200) < 700
    wizard_panel = ft.Container(
        width=None if wizard_is_mobile else 720,
        height=None if wizard_is_mobile else 800,
        expand=wizard_is_mobile,
        padding=20 if wizard_is_mobile else 30,
        border_radius=12,
        bgcolor=ft.Colors.SURFACE_CONTAINER,
        content=ft.Column(
            controls=[
                ft.Text("👤 Username to Display Name", size=32, weight=ft.FontWeight.BOLD),
                ft.Text(
                    "Change the display names of each player.", 
                    size=20, color="grey400"
                ),
                ft.Divider(height=20),
                
                ft.Container(content=mapping_rows, expand=True, margin=ft.Margin(0, 10, 0, 10)),
                
                ft.Divider(height=20),
                ft.Row(
                    controls=[
                        ft.TextButton(
                            "Skip", 
                            icon=ft.Icons.SKIP_NEXT, 
                            on_click=lambda e: page.run_task(handle_skip_wizards, e),
                            style=ft.ButtonStyle(color="grey500")
                        ),
                        ft.Row([
                            ft.ElevatedButton(
                                "Add Player", 
                                icon=ft.Icons.ADD_REACTION, 
                                on_click=handle_add_custom_player, 
                                bgcolor="purple700", 
                                color="white"
                            ),
                            ft.ElevatedButton(
                                "Save", 
                                icon=ft.Icons.CHECK_CIRCLE, 
                                on_click=lambda e: page.run_task(handle_save_and_sync, e), 
                                bgcolor="green700", 
                                color="white"
                            )
                        ], spacing=10)
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                )
            ]
        )
    )

    page.add(wizard_panel)
    page.update()

    await wizard_done.wait()

async def loading_gateway(page: ft.Page):
    """The central gateway layout that automatically handles the intercepted Spotify flow."""
    page.update()
    page.title = "Eric the Data Manager Portal"
    page.theme_mode = ft.ThemeMode.DARK
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    is_mobile = (page.width or 1200) < 600
    field_width = min(380, (page.width or 380) - 40)

    league_id_field = ft.TextField(label="Music League ID/URL", width=field_width, hint_text="e.g., 4a7b9...")
    admin_password_field = ft.TextField(label="Admin Password (Required for Scraping)", width=field_width, password=True, can_reveal_password=True)
    session_cookie_field = ft.TextField(
        label="Music League Session Cookie",
        width=field_width,
        password=True,
        can_reveal_password=True,
        hint_text="Paste from your browser's dev tools (Application > Cookies)"
    )
    browser_dropdown = ft.Dropdown(
        label="Browser Used for Scraping",
        value="chromium",
        width=field_width,
        options=[
            ft.dropdown.Option("chromium", "Chromium (Google Chrome stable)"),
            ft.dropdown.Option("firefox", "Mozilla Firefox (Geckodriver)")
        ]
    )
    error_text = ft.Text(value="", color="red", size=20, weight=ft.FontWeight.BOLD)
    main_menu_container = ft.Ref[ft.Column]()

    async def execute_portal_pipeline(is_admin_mode: bool):
        l_id = league_id_field.value.strip()
        pwd = admin_password_field.value.strip()
        raw_id_input = league_id_field.value.strip()
        
        if not raw_id_input:
            error_text.value = "Error: A valid Music League ID parameter is required."
            page.update()
            return
            
        if "musicleague.com" in raw_id_input:
            try:
                parts = raw_id_input.split("/l/")
                l_id = parts[1].strip("/").split("/")[0]
            except Exception:
                l_id = raw_id_input
        else:
            l_id = raw_id_input
            
        if not l_id:
            error_text.value = "Error: A valid Music League ID parameter is required."
            page.update()
            return
            
        hashed_pwd = hashlib.sha256(pwd.encode()).hexdigest() if pwd else ""
        session_cookie_value = session_cookie_field.value.strip() if session_cookie_field.value else ""
        
        if is_admin_mode:
            if not pwd:
                error_text.value = "Error: Admin Password is required to scrape for data."
                page.update() 
                return
            if not session_cookie_value:
                error_text.value = "Error: Paste your Music League session cookie before running a Sync!"
                error_text.color = "red"
                page.update()
                return

        main_menu_container.current.visible = False
        page.update() 
        
        progress_bar, status_text = show_loading_page(page)
        
        try:
            progress_bar.value = 0.15
            status_text.value = "Contacting database..."
            page.update() 
            
            await asyncio.to_thread(clear_search_processor_globals)
            db_cache_payload = await asyncio.to_thread(get_league_data_from_postgres, l_id)

            has_no_history = True
            if db_cache_payload:
                if db_cache_payload.get("rounds") or db_cache_payload.get("players"):
                    has_no_history = False

            if is_admin_mode or has_no_history:
                progress_bar.value = 0.35
                status_text.value = f"Verifying pipeline admin configuration rules..."
                page.update() 
                
                if db_cache_payload and db_cache_payload.get("admin_password_hash"):
                    if not verify_admin_password_hash(l_id, hashed_pwd):
                        raise ValueError("Admin Authentication Failed: Invalid secret key for this league ID.")
                
                progress_bar.value = 0.55
                status_text.value = "Extracting league data..."
                page.update() 
                
                updated_payload = await asyncio.to_thread(
                    run_pipeline_migration, l_id, browser_dropdown.value, session_cookie_value, db_cache_payload or {}
                )
                
                progress_bar.value = 0.70
                status_text.value = "Saving data..."
                page.update() 
                
                await asyncio.to_thread(
                    save_league_data_to_postgres, l_id, hashed_pwd, updated_payload, browser_dropdown.value
                )
                db_cache_payload = updated_payload

            progress_bar.value = 0.80
            status_text.value = "Initializing data storage..."
            page.update() 
            await asyncio.to_thread(initialize_memory_cache, db_cache_payload)

            progress_bar.value = 0.95
            status_text.value = "Compiling profiles & preparing search..."
            page.update() 
            
            await asyncio.to_thread(build_static_dashboard_cache, db_cache_payload)
            await asyncio.to_thread(init_search_cache)

            progress_bar.value = 0.9
            status_text.value = "Rendering dashboard — building player profiles takes a bit longer..."
            page.update()

            def _dashboard_progress(fraction: float, message: str):
                progress_bar.value = min(0.99, 0.9 + fraction * 0.1)
                status_text.value = message
                page.update()

            page.horizontal_alignment = ft.CrossAxisAlignment.START
            page.vertical_alignment = ft.MainAxisAlignment.START

            await main_dashboard(page, progress_callback=_dashboard_progress)
            
        except Exception as ex:
            progress_bar.visible = False
            status_text.visible = False
            error_text.value = str(ex)
            main_menu_container.current.visible = True
            page.update()

    main_menu_container.current = ft.Column(
        ref=main_menu_container,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=15,
        scroll=ft.ScrollMode.HIDDEN,
        controls=[
            ft.Text("🎵 Eric the Data Manager", size=28 if is_mobile else 44, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
            ft.Text("Music League Data Manager", size=16 if is_mobile else 20, color="grey400"),
            ft.Container(height=10),
            league_id_field,
            error_text,
            
            ft.ResponsiveRow(
                alignment=ft.MainAxisAlignment.CENTER,
                controls=[
                    ft.Container(
                        col={"xs": 12, "sm": 12, "md": 6, "lg": 5},
                        content=ft.Card(
                            content=ft.Container(
                                padding=20,
                                content=ft.Column([
                                    ft.Text("League Member Portal", size=20, weight=ft.FontWeight.BOLD),
                                    ft.Text("View live leaderboards, vote matrices, track profiles, and round stats instantly.", size=18, color="grey"),
                                    ft.Container(height=32),
                                    ft.ElevatedButton("View Analytics",
                                                      on_click=lambda e: page.run_task(execute_portal_pipeline, False),
                                                      icon=ft.Icons.VIEW_AGENDA,bgcolor="blue700",color="white"
                                                    )
                                    ], 
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                                )
                            )
                    ),
                    ft.Container(
                        col={"xs": 12, "sm": 12, "md": 6, "lg": 5},
                        content=ft.Card(
                            content=ft.Container(
                                padding=20,
                                content=ft.Column([
                                    ft.Text("🛠️ Admin Panel", size=20, weight=ft.FontWeight.BOLD),
                                    ft.Text("Initialize new leagues or pull results of new rounds.", size=16, color="grey"),
                                    admin_password_field,
                                    session_cookie_field,
                                    browser_dropdown,
                                    ft.Container(height=5),
                                    ft.ElevatedButton(
                                        "Sync Data",
                                        on_click=lambda e: page.run_task(execute_portal_pipeline, True),
                                        icon=ft.Icons.RUN_CIRCLE,
                                        bgcolor="amber700",
                                        color="white"
                                    )
                                ],
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER, 
                                spacing=10
                                )
                            )
                        )
                    )
                ]
            )
        ]
    )

    page.add(main_menu_container.current)
    
root_project_directory = os.getcwd()
production_assets_path = os.path.join(root_project_directory, "assets")

app = flet_fastapi.app(loading_gateway, assets_dir=production_assets_path)

def fetch_avatar_base64_raw(url: str) -> str:
    if not url:
        return ""
    try:
        with httpx.Client() as client:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            response = client.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                return base64.b64encode(response.content).decode("utf-8")
    except Exception as e:
        print(f"Internal proxy download failed for url {url}: {e}")
        return ""
    
@app.get("/proxy-avatar")
async def proxy_avatar(url: str):
    base64_data = await asyncio.to_thread(fetch_avatar_base64_raw, url)
    if base64_data:
        return {"base64_data": base64_data}
    return {"error": "Failed to fetch remote asset image data"}