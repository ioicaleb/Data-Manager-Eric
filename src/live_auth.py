"""
live_auth.py - Live, admin-visible browser login for capturing a fresh
Music League session cookie, as a fallback when a stored/pasted cookie
is missing or has expired.
"""

import subprocess
import time
import os
import atexit

from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.chrome.options import Options as ChromeOptions

DISPLAY_NUM = 99
DISPLAY = f":{DISPLAY_NUM}"
VNC_PORT = 5900
NOVNC_PORT = 6080
SCREEN_GEOMETRY = "1280x1024x24"

_active_session = {
    "in_use": False,
    "driver": None,
    "xvfb_proc": None,
    "x11vnc_proc": None,
    "websockify_proc": None,
}


def is_live_session_active() -> bool:
    return _active_session["in_use"]


def _start_process(cmd: list[str], name: str) -> subprocess.Popen:
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    print(f"[live_auth] Started {name} (pid={proc.pid})")
    return proc


def start_live_login_session(config: dict):
    """
    Boots the virtual display stack and launches a real, visible browser
    into it. Returns the Selenium driver so the caller can navigate it
    to the Music League login page. Raises RuntimeError if a session is
    already active.
    """
    if _active_session["in_use"]:
        raise RuntimeError("A live login session is already in progress. Only one is supported at a time.")

    _active_session["in_use"] = True

    xvfb_proc = _start_process(
        ["Xvfb", DISPLAY, "-screen", "0", SCREEN_GEOMETRY],
        "Xvfb",
    )
    time.sleep(1)

    x11vnc_proc = _start_process(
        ["x11vnc", "-display", DISPLAY, "-nopw", "-forever", "-shared", "-rfbport", str(VNC_PORT), "-quiet"],
        "x11vnc",
    )
    time.sleep(1)

    websockify_proc = _start_process(
        [
            "websockify",
            "--web", "/usr/share/novnc",
            str(NOVNC_PORT),
            f"localhost:{VNC_PORT}",
        ],
        "websockify/noVNC",
    )
    time.sleep(1)

    _active_session["xvfb_proc"] = xvfb_proc
    _active_session["x11vnc_proc"] = x11vnc_proc
    _active_session["websockify_proc"] = websockify_proc

    env = os.environ.copy()
    env["DISPLAY"] = DISPLAY

    browser_type = config.get("browser_type", "chromium")
    if browser_type == "firefox":
        options = FirefoxOptions()
        service = FirefoxService(executable_path="/usr/local/bin/geckodriver")
        os.environ["DISPLAY"] = DISPLAY
        driver = webdriver.Firefox(options=options, service=service)
    else:
        options = ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        os.environ["DISPLAY"] = DISPLAY
        driver = webdriver.Chrome(options=options)

    _active_session["driver"] = driver
    driver.get("https://app.musicleague.com/")

    print(f"[live_auth] Visible browser ready. Admin view available via noVNC on port {NOVNC_PORT}.")
    return driver


def capture_session_cookie(cookie_name: str = "app.musicleague.com", domain: str = "app.musicleague.com"):
    """
    Reads the cookie from the live session's browser. Call this after
    the admin confirms they've finished logging in. Returns the cookie
    value, or None if it isn't present yet (login not actually complete).
    """
    driver = _active_session.get("driver")
    if driver is None:
        raise RuntimeError("No active live login session to capture from.")

    driver.get(f"https://{domain}/l/")
    cookies = driver.get_cookies()
    match = next((c for c in cookies if c.get("name") == cookie_name), None)
    return match.get("value") if match else None


def end_live_login_session():
    """Tears down the browser and the whole virtual display stack."""
    driver = _active_session.get("driver")
    if driver is not None:
        try:
            driver.quit()
        except Exception as e:
            print(f"[live_auth] Error closing live-login driver: {e}")

    for key in ("websockify_proc", "x11vnc_proc", "xvfb_proc"):
        proc = _active_session.get(key)
        if proc is not None:
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except Exception as e:
                print(f"[live_auth] Error stopping {key}: {e}")

    _active_session.update({
        "in_use": False,
        "driver": None,
        "xvfb_proc": None,
        "x11vnc_proc": None,
        "websockify_proc": None,
    })
    print("[live_auth] Live login session ended, virtual display stack torn down.")

atexit.register(lambda: end_live_login_session() if _active_session["in_use"] else None)