import os
import sys

# Calculate absolute paths to the project root directory
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__)) # points to /src
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)               # points to /Data-Manager-Eric

# Force Python to search the root directory and the src directory for module names
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

import flet as ft
import hashlib
import flet_fastapi

# Import your multi-tab visual containers
from tabs.player_stats import generate_profile_tab
from tabs.matrix import generate_matrix_tab
from tabs.standings import generate_standings_tab
from tabs.rounds import generate_rounds_tab
from tabs.song_check import generate_songs_tab

# Import cloud processing modules
from data_processing.cache_manager import initialize_memory_cache, get_master_memory_payload
from data_processing.search_processor import clear_search_processor_globals, init_search_cache
from data_processing.cache_builder import build_static_dashboard_cache
from data_processing.data_processor import save_app_data
from data_collection.data_collector import run_pipeline_migration

# ---------------------------------------------------------
# 1. CLOUD REPLAY & DATABASE LAYER CONFIGURATION
# ---------------------------------------------------------

def get_league_data_from_postgres(league_id: str) -> dict:
    """Safely retrieves the raw data dictionary from your Render PostgreSQL instance."""
    import psycopg2
    from psycopg2.extras import RealDictCursor
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    if not DATABASE_URL:
        # Prevent runtime connection crash locally if no env variable is assigned
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

def save_league_data_to_postgres(league_id: str, secret_pwd_hash: str, payload: dict, cookie: str, browser: str):
    """Saves or updates your unified compiled parameters inside PostgreSQL JSONB."""
    import psycopg2
    import json
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    conn = psycopg2.connect(DATABASE_URL, sslmode="require")
    cur = conn.cursor()
    
    # Check existence
    cur.execute("SELECT 1 FROM music_leagues WHERE league_id = %s;", (league_id,))
    exists = cur.fetchone()
    
    if exists:
        cur.execute(
            "UPDATE music_leagues SET scraped_data = %s, session_cookie = %s, browser_type = %s WHERE league_id = %s;",
            (json.dumps(payload), cookie, browser, league_id)
        )
    else:
        cur.execute(
            "INSERT INTO music_leagues (league_id, admin_password_hash, session_cookie, browser_type, scraped_data) VALUES (%s, %s, %s, %s, %s);",
            (league_id, secret_pwd_hash, cookie, browser, json.dumps(payload))
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

# ---------------------------------------------------------
# 2. THE MULTI-TAB VISUAL DASHBOARD
# ---------------------------------------------------------
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
        main_dashboard(page_obj, start_tab_index=2)
    
    # Pull dynamic parameters safely from the newly generated internal structures
    standings_container = generate_standings_tab(page)
    matrix_container = generate_matrix_tab(page)
    profiles_container = generate_profile_tab(page, return_callback)
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

# ---------------------------------------------------------
# 3. SHOW LOADING PAGE WITH VISUAL PROGRESS
# ---------------------------------------------------------
def show_loading_page(page: ft.Page):
    """Renders your original visual pipeline loading bars on the active screen canvas."""
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
    return progress_bar, status_text

# ---------------------------------------------------------
# 4. UNIFIED GATEWAY INTERFACE
# ---------------------------------------------------------
async def loading_gateway(page: ft.Page):
    """The central gateway layout that enables players to access stats and admins to run setups."""
    page.title = "Eric the Data Manager Portal"
    page.theme_mode = ft.ThemeMode.DARK
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    # Interactive Form Properties
    league_id_field = ft.TextField(label="Music League ID / URL Slug", width=380, hint_text="e.g., 4a7b9...")
    admin_password_field = ft.TextField(label="Admin Secret Key (Required for Scraping)", width=380, password=True, can_reveal_password=True)
    cookie_field = ft.TextField(label="Updated Session Cookie (Required for Scraping)", width=380, password=True)
    
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

    def execute_portal_pipeline(is_admin_mode: bool):
        l_id = league_id_field.value.strip()
        pwd = admin_password_field.value.strip()
        cookie = cookie_field.value.strip()
        browser_type = browser_dropdown.value
        
        if not l_id:
            error_text.value = "Error: A valid Music League ID parameter is required."
            page.update()
            return
            
        hashed_pwd = hashlib.sha256(pwd.encode()).hexdigest() if pwd else ""
        
        if is_admin_mode and (not pwd or not cookie):
            error_text.value = "Error: Admin Password and Session Cookie are both required to trigger a scrape task."
            page.update()
            return

        # Hide the control forms and switch over to your loading bar progress state layout
        main_menu_container.current.visible = False
        page.update()
        
        progress_bar, status_text = show_loading_page(page)
        page.update()
        
        try:
            # Step 1: Clear old search indexes and download row entries from Postgres
            progress_bar.value = 0.1
            status_text.value = "Contacting database storage layers..."
            page.update()
            
            clear_search_processor_globals()
            db_cache_payload = get_league_data_from_postgres(l_id)

            # Step 2: Handle active Selenium scraping procedures if Admin requested it
            if is_admin_mode:
                progress_bar.value = 0.3
                status_text.value = "Authenticating admin credentials..."
                page.update()
                
                # Check for password collisions if this league row already exists
                if db_cache_payload and not verify_admin_password_hash(l_id, hashed_pwd):
                    raise ValueError("Admin Authentication Failed: Invalid secret key for this league ID.")
                    
                progress_bar.value = 0.4
                status_text.value = "Launching headless container driver... Scraping Music League..."
                page.update()
                
                # Triggers your refactored data_collector selenium modules directly
                updated_payload = run_pipeline_migration(l_id, cookie, browser_type, db_cache_payload)
                
                # Commit freshly updated maps back to Postgres instantly
                save_league_data_to_postgres(l_id, hashed_pwd, updated_payload, cookie, browser_type)
                db_cache_payload = updated_payload

            # Check if player requested data for a completely empty or missing league ID
            if not db_cache_payload:
                raise ValueError("Specified League ID has no parsed history. An Admin must run a Force Crawl first.")

            # Step 3: Seed our memory maps using cache_manager functions
            progress_bar.value = 0.6
            status_text.value = "Hydrating in-memory state caches..."
            page.update()
            initialize_memory_cache(db_cache_payload)

            # Step 4: Run pre-computation processing matrix logic steps
            progress_bar.value = 0.8
            status_text.value = "Compiling analytics profiles..."
            page.update()
            build_static_dashboard_cache(db_cache_payload)
            init_search_cache()

            # Step 5: Complete tasks
            progress_bar.value = 1.0
            status_text.value = "Done! Loading analytics views..."
            page.update()
            
            save_app_data()
            
            # Clean loading overlay layouts out of the screen canvas view
            page.controls.clear()
            page.horizontal_alignment = ft.CrossAxisAlignment.START
            page.vertical_alignment = ft.MainAxisAlignment.START
            
            main_dashboard(page)
            page.update()
            
        except Exception as ex:
            # Crash protection: Reset back onto clean error landing views
            print(f"Gateway pipeline dropped: {ex}")
            page.controls.clear()
            page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
            page.vertical_alignment = ft.MainAxisAlignment.CENTER
            page.add(
                ft.Icon(ft.Icons.ERROR_OUTLINE, color=ft.Colors.RED, size=50),
                ft.Text(f"Pipeline failure occurred:\n{str(ex)}", text_align=ft.TextAlign.CENTER, color=ft.Colors.RED, size=16),
                ft.ElevatedButton("Return to Portal Gateway", on_click=lambda _: page.go("/"))
            )
            page.update()

    # Layout design for your entry dashboard cards
    page.add(
        ft.Column(
            ref=main_menu_container,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=15,
            controls=[
                ft.Text("🎵 Eric the Data Manager", size=38, weight=ft.FontWeight.BOLD),
                ft.Text("Music League Cloud Analytics Portal Engine", size=14, color="grey400"),
                ft.Container(height=10),
                
                # Shared identity field
                league_id_field,
                error_text,
                
                ft.Row([
                    # Player Card Action
                    ft.Card(
                        content=ft.Container(
                            padding=20, width=280,
                            content=ft.Column([
                                ft.Text("League Member Portal", size=16, weight=ft.FontWeight.BOLD),
                                ft.Text("View live leaderboards, vote matrices, track profiles, and round stats instantly.", size=12, color="grey"),
                                ft.Container(height=48), # Spacer spacing balance
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
                    
                    # Admin Card Action
                    ft.Card(
                        content=ft.Container(
                            padding=20, width=420,
                            content=ft.Column([
                                ft.Text("🛠️ League Setup & Scraping Panel", size=16, weight=ft.FontWeight.BOLD),
                                ft.Text("Initialize new leagues or fetch fresh results via headless web crawlers.", size=12, color="grey"),
                                admin_password_field,
                                cookie_field,
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
