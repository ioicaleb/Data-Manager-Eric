import os
import psycopg2
import asyncio
import sys
import flet as ft
import hashlib
import flet.fastapi as flet_fastapi

# Calculate absolute paths to the project root directory
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__)) # points to /src
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)               # points to /Data-Manager-Eric

# Force Python to search the root directory and the src directory for module names
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

# Import your multi-tab visual containers
from tabs.player_stats import generate_profile_tab
from tabs.matrix import generate_matrix_tab
from tabs.standings import generate_standings_tab
from tabs.rounds import generate_rounds_tab
from tabs.song_check import generate_songs_tab

# Import cloud processing modules
from data_processing.cache_manager import initialize_memory_cache
from data_processing.search_processor import clear_search_processor_globals, init_search_cache
from data_processing.cache_builder import build_static_dashboard_cache
from data_processing.data_processor import save_app_data
from data_collection.data_collector import run_pipeline_migration

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is missing from your local session.")

# Connect and initialize the schema
conn = psycopg2.connect(DATABASE_URL, sslmode="require")
cur = conn.cursor()

# Raw schema design mirroring your jsonb compiled structures
create_table_query = """
CREATE TABLE IF NOT EXISTS music_leagues (
    league_id VARCHAR(255) PRIMARY KEY,
    admin_password_hash VARCHAR(255),
    browser_type VARCHAR(50),
    scraped_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

print("Initializing music_leagues table structure...")
cur.execute(create_table_query)
conn.commit()

cur.close()
conn.close()
print("Database schema successfully generated!")

# ---------------------------------------------------------
# 1. CLOUD REPLAY & DATABASE LAYER CONFIGURATION
# ---------------------------------------------------------

def get_league_data_from_postgres(league_id: str) -> dict:
    """Safely retrieves the raw data dictionary from your Render PostgreSQL instance."""
    import psycopg2
    from psycopg2.extras import RealDictCursor
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
    """Saves or updates your unified compiled parameters inside PostgreSQL JSONB."""
    import psycopg2
    import json
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
            "INSERT INTO music_leagues (league_id, admin_password_hash, browser_type, scraped_data) VALUES (%s, %s, %s, %s, %s);",
            (league_id, secret_pwd_hash, browser, json.dumps(payload))
        )
    conn.commit()
    cur.close()
    conn.close()

def verify_admin_password_hash(league_id: str, submitted_password_hash: str) -> bool:
    """Verifies the admin password string against the database hash for existing rows."""
    import psycopg2
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

def main_dashboard(page: ft.Page, start_tab_index=0): 
    """Your original visual layout manager. Renders analytics from active memory cache."""
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

    def return_callback(page_obj):
        page_obj.controls.clear()
        main_dashboard(page_obj, start_tab_index=2)
    
    standings_container = generate_standings_tab(page)
    matrix_container = generate_matrix_tab(page)
    
    try:
        profiles_container = generate_profile_tab(page, lambda p: return_callback(p))
        if profiles_container is None:
            raise ValueError("Profile tab function returned None value string configuration.")
    except Exception as e:
        print(f"Warning: profiles_container failed to initialize: {e}")
        profiles_container = ft.Container(
            content=ft.Text(f"Profiles tab initialization error: {str(e)}", color="amber700"),
            padding=20
        )

    rounds_container = generate_rounds_tab(page)
    songs_container = generate_songs_tab(page)


    tab_view = ft.Tabs(
        length=5,
        selected_index=start_tab_index,
        expand=True,
        content=ft.Column(
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
    """Renders a visual pipeline loading bar layout on the screen."""
    page.controls.clear()
    
    loading_text = ft.Text("Eric is Processing Your League", size=32, weight=ft.FontWeight.BOLD)
    
    progress_bar = ft.ProgressBar(width=400, color="purple", value=0.0)
    status_text = ft.Text("Initializing secure runtime containers...", size=18, color="grey400")
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
            ft.Text("Please do not close this browser window.", size=12, color="grey600"),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        expand=True
    )
    
    page.add(loading_layout)
    page.update()
    
    return progress_bar, status_text

def show_username_mapping_wizard(page: ft.Page, payload: dict, league_id: str, pwd_hash: str):
    """
    Renders an interactive administrative onboarding panel to map 
    scraped system usernames directly to clean visual profile names.
    """
    page.title = "Username Wizard"
    
    existing_map = payload.get("username_mapping") or {}
    scraped_users = list(payload.get("avatars", {}).keys())
    
    if "[Left the league]" in scraped_users:
        scraped_users.remove("[Left the league]")

    mapping_rows = ft.Column(spacing=15, scroll=ft.ScrollMode.HIDDEN, expand=True)
    text_fields_registry = {}

    def build_mapping_row(username: str, prefill_value: str = ""):
        input_field = ft.TextField(
            label="Preferred Display Name",
            value=prefill_value or username,
            width=280,
            hint_text="e.g., Eric S."
        )
        text_fields_registry[username] = input_field
        
        return ft.Container(
            padding=10,
            border_radius=8,
            bgcolor=ft.Colors.GREY_900 if page.theme_mode == ft.ThemeMode.DARK else ft.Colors.GREY_100,
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.PERSON_OUTLINE, color="purple"),
                    ft.Text(username, size=16, weight=ft.FontWeight.BOLD, width=200),
                    ft.Icon(ft.Icons.ARROW_FORWARD, color="grey600"),
                    input_field
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            )
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

    def handle_save_and_sync(e):
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

        payload["username_mapping"] = compiled_username_map
        payload["players"] = new_players_list

        initialize_memory_cache(payload)
        build_static_dashboard_cache(payload)
        init_search_cache()
        save_app_data()

        save_league_data_to_postgres(
            league_id=league_id,
            secret_pwd_hash=pwd_hash,
            payload=payload,
            browser=payload.get("browser_type", "chromium")
        )

        page.controls.clear()
        page.horizontal_alignment = ft.CrossAxisAlignment.START
        page.vertical_alignment = ft.MainAxisAlignment.START
        main_dashboard(page)
        page.update()

    def handle_skip_wizards(e):
        if not payload.get("username_mapping"):
            payload["username_mapping"] = {u: u for u in scraped_users}
            
        initialize_memory_cache(payload)
        build_static_dashboard_cache(payload)
        init_search_cache()
        
        page.controls.clear()
        page.horizontal_alignment = ft.CrossAxisAlignment.START
        page.vertical_alignment = ft.MainAxisAlignment.START
        main_dashboard(page)
        page.update()

    wizard_panel = ft.Container(
        width=720,
        height=800,
        padding=30,
        border_radius=12,
        bgcolor=ft.Colors.SURFACE_CONTAINER,
        content=ft.Column(
            controls=[
                ft.Text("👤 Username to Display Name", size=26, weight=ft.FontWeight.BOLD),
                ft.Text(
                    "Change the display names of each player.", 
                    size=14, color="grey400"
                ),
                ft.Divider(height=20),
                
                ft.Container(content=mapping_rows, expand=True, margin=ft.Margin(0, 10, 0, 10)),
                
                ft.Divider(height=20),
                ft.Row(
                    controls=[
                        ft.TextButton(
                            "Skip", 
                            icon=ft.Icons.SKIP_NEXT, 
                            on_click=handle_skip_wizards,
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
                                on_click=handle_save_and_sync, 
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

async def loading_gateway(page: ft.Page):
    """The central gateway layout that enables players to access stats and admins to run setups."""
    page.title = "Eric the Data Manager Portal"
    page.theme_mode = ft.ThemeMode.DARK
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    league_id_field = ft.TextField(label="Music League ID/URL", width=380, hint_text="e.g., 4a7b9...")
    admin_password_field = ft.TextField(label="Admin Secret Key (Required for Scraping)", width=380, password=True, can_reveal_password=True)
    
    browser_dropdown = ft.Dropdown(
        label="Target Headless Webdriver Engine",
        value="chromium",
        width=380,
        options=[
            ft.dropdown.Option("chromium", "Chromium (Google Chrome stable)"),
            ft.dropdown.Option("firefox", "Mozilla Firefox (Geckodriver)")
        ]
    )
    
    error_text = ft.Text(value="", color="red", size=14, weight=ft.FontWeight.BOLD)
    main_menu_container = ft.Ref[ft.Column]()

    async def execute_portal_pipeline(is_admin_mode: bool):
        l_id = league_id_field.value.strip()
        pwd = admin_password_field.value.strip()
        browser_type = browser_dropdown.value

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
        
        if is_admin_mode and (not pwd):
            error_text.value = "Error: Admin Password is required to trigger a scrape task."
            page.update() 
            return

        main_menu_container.current.visible = False
        page.update() 
        
        progress_bar, status_text = show_loading_page(page)
        
        try:
            progress_bar.value = 0.15
            status_text.value = "Contacting Render PostgreSQL instance..."
            page.update() 
            
            await asyncio.to_thread(clear_search_processor_globals)
            db_cache_payload = await asyncio.to_thread(get_league_data_from_postgres, l_id)

            has_no_history = True
            if db_cache_payload:
                if db_cache_payload.get("rounds") or db_cache_payload.get("players"):
                    has_no_history = False

            if is_admin_mode or has_no_history:
                progress_bar.value = 0.35
                status_text.value = f"Opening Music League..."
                page.update() 
                
                if db_cache_payload and db_cache_payload.get("admin_password_hash"):
                    if not verify_admin_password_hash(l_id, hashed_pwd):
                        raise ValueError("Admin Authentication Failed: Invalid secret key for this league ID.")
                
                progress_bar.value = 0.55
                status_text.value = "Extracting league results..."
                page.update() 
                
                updated_payload = await asyncio.to_thread(
                    run_pipeline_migration, l_id, browser_type, db_cache_payload or {}
                )
                
                progress_bar.value = 0.70
                status_text.value = "Saving data..."
                page.update() 
                
                await asyncio.to_thread(
                    save_league_data_to_postgres, l_id, hashed_pwd, updated_payload, browser_type
                )
                db_cache_payload = updated_payload

            if not db_cache_payload or (not db_cache_payload.get("rounds") and not db_cache_payload.get("players")):
                raise ValueError("Specified League ID has no parsed history. An Admin must run a Force Crawl first.")

            username_map = db_cache_payload.get("username_mapping", {})
            scraped_usernames = db_cache_payload.get("avatars", {}).keys() 

            has_unmapped = any(user not in username_map for user in scraped_usernames)
            if (not username_map or has_unmapped) and is_admin_mode:
                status_text.value = "Launching User Mapping Wizard..."
                page.update()
                
                page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
                page.vertical_alignment = ft.MainAxisAlignment.CENTER
                page.controls.clear()
                
                show_username_mapping_wizard(page, db_cache_payload, l_id, hashed_pwd)

            progress_bar.value = 0.80
            status_text.value = "Hydrating local analytical memory state caches..."
            page.update() 
            await asyncio.to_thread(initialize_memory_cache, db_cache_payload)

            progress_bar.value = 0.95
            status_text.value = "Compiling analytics profiles & generating search indexes..."
            page.update() 
            
            await asyncio.to_thread(build_static_dashboard_cache, db_cache_payload)
            await asyncio.to_thread(init_search_cache)
            await asyncio.to_thread(save_app_data)

            progress_bar.value = 1.0
            status_text.value = "Done! Launching dashboard analytics..."
            page.update() 
            
            page.horizontal_alignment = ft.CrossAxisAlignment.START
            page.vertical_alignment = ft.MainAxisAlignment.START
            page.controls.clear()
            
            main_dashboard(page)
            page.update() 
            
        except ValueError as val_ex:
            print(f"Gateway pipeline warning: {val_ex}")
            page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
            page.vertical_alignment = ft.MainAxisAlignment.CENTER
            page.controls.clear()
            
            error_text.value = str(val_ex)
            if main_menu_container.current is not None:
                main_menu_container.current.visible = True
                page.add(ft.Column(ref=main_menu_container, controls=page.controls)) 
            else:
                error_text.value = f"Warning: {str(val_ex)}"
                page.add(
                    ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=15,
                        controls=[
                            ft.Text("🎵 Eric the Data Manager", size=38, weight=ft.FontWeight.BOLD),
                            league_id_field,
                            error_text,
                            ft.ElevatedButton("Return to Main Menu", on_click=lambda _: page.go("/"))
                        ]
                    )
                )
            
            page.snack_bar = ft.SnackBar(content=ft.Text(str(val_ex), color="white"), bgcolor="amber700")
            page.snack_bar.open = True
            page.update()

        except Exception as ex:
            print(f"Gateway pipeline dropped: {ex}")
            page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
            page.vertical_alignment = ft.MainAxisAlignment.CENTER
            page.controls.clear()
            page.add(
                ft.Icon(ft.Icons.ERROR_OUTLINE, color=ft.Colors.RED, size=50),
                ft.Text(f"System pipeline failure occurred:\n{str(ex)}", text_align=ft.TextAlign.CENTER, color=ft.Colors.RED, size=16),
                ft.ElevatedButton("Return to Portal Gateway", on_click=lambda _: page.go("/"))
            )
            page.update()

    page.add(
        ft.Column(
            ref=main_menu_container,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=15,
            controls=[
                ft.Text("🎵 Eric the Data Manager", size=38, weight=ft.FontWeight.BOLD),
                ft.Text("Music League Cloud Analytics Portal Engine", size=14, color="grey400"),
                ft.Container(height=10),
                
                league_id_field,
                error_text,
                
                ft.Row([
                    ft.Card(
                        content=ft.Container(
                            padding=20, width=280,
                            content=ft.Column([
                                ft.Text("League Member Portal", size=16, weight=ft.FontWeight.BOLD),
                                ft.Text("View live leaderboards, vote matrices, track profiles, and round stats instantly.", size=12, color="grey"),
                                ft.Container(height=48), 
                                ft.ElevatedButton(
                                    "View Analytics", 
                                    on_click=lambda e: page.run_task(execute_portal_pipeline, False), 
                                    icon=ft.Icons.VIEW_AGENDA, 
                                    bgcolor="blue700", 
                                    color="white"
                                )
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                        )
                    ),
                    
                    ft.Card(
                        content=ft.Container(
                            padding=20, width=420,
                            content=ft.Column([
                                ft.Text("🛠️ League Setup & Scraping Panel", size=16, weight=ft.FontWeight.BOLD),
                                ft.Text("Initialize new leagues or fetch fresh results via headless web crawlers.", size=12, color="grey"),
                                admin_password_field,
                                browser_dropdown,
                                ft.ElevatedButton(
                                    "Force Crawl / Sync Data", 
                                    on_click=lambda e: page.run_task(execute_portal_pipeline, True), 
                                    icon=ft.Icons.RUN_CIRCLE, 
                                    bgcolor="amber700", 
                                    color="white"
                                )
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10)
                        )
                    )
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=20)
            ]
        )
    )
    page.update()


app = flet_fastapi.app(loading_gateway)

import base64
import httpx

def fetch_avatar_base64_raw(url: str) -> str:
    """Downloads an external CDN profile picture and encodes it directly into a clean Base64 string."""
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
    base64_data = fetch_avatar_base64_raw(url)
    if base64_data:
        return {"base64_data": base64_data}
    return {"error": "Failed to fetch remote asset image data"}

