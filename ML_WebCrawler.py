import json
import os
import time

from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

code = ""  # Global variable to store the Spotify verification code

def load_config(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def wait_click(driver, locator, timeout=5):
    WebDriverWait(driver, timeout).until(EC.element_to_be_clickable(locator)).click()


def fill_email(driver, locator, value, timeout=5):
    elem = WebDriverWait(driver, timeout).until(EC.visibility_of_element_located(locator))
    elem.send_keys(value)

def fill_code(driver, locator, value, timeout=5):
    elems = WebDriverWait(driver, timeout).until(EC.visibility_of_all_elements_located(locator))
    for elem, digit in zip(elems, value):
        elem.send_keys(digit)

def click_by_text(driver, texts, timeout=5):
    for text in texts:
        try:
            xpath = (
                "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
                "'abcdefghijklmnopqrstuvwxyz'), '{}')]"
                "|//a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
                "'abcdefghijklmnopqrstuvwxyz'), '{}')]"
                "|//input[@value='{}']"
            ).format(text.lower(), text.lower(), text)
            WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            ).click()
            return True
        except TimeoutException:
            continue
    return False


def login_to_music_league(driver, config):
    login_url = config.get("league_url")
    driver.get(login_url)

    # Click the Music League login option that redirects to Spotify
    click_by_text(driver, ["continue with spotify", "log in with spotify", "spotify"])

    # Try a few common Spotify login button/link selectors if the first attempt fails
    if "spotify.com" not in driver.current_url.lower():
        for locator in [
            (By.CSS_SELECTOR, "a[href*='spotify']"),
            (By.CSS_SELECTOR, "button[href*='spotify']"),
            (By.XPATH, "//button[contains(., 'Spotify')]"),
            (By.XPATH, "//a[contains(., 'Spotify')]"),
        ]:
            try:
                wait_click(driver, locator)
                break
            except TimeoutException:
                continue

    # Spotify login page
    spotify_username = config.get("spotify_username") or config.get("email")
    
    if not spotify_username:
        raise ValueError("Config file must contain spotify_username")

    # Fill username
    for locator in [
        (By.ID, "username"),
        (By.CSS_SELECTOR, "input[id='username']"),
        (By.CSS_SELECTOR, "input[type='text']"),
    ]:
        try:
            fill_email(driver, locator, spotify_username)
            click_by_text(driver, "Continue")
            break
        except TimeoutException:
            continue

    # Fill code
    for locator in [
        (By.CSS_SELECTOR, "div[data-testid='phonelogin-code'] > input"),
        (By.CSS_SELECTOR, "input[inputmode='numeric']"),
    ]:
        try:
            global code
            if code == "":
                code = input("Enter the Spotify verification code: ")
            fill_code(driver, locator, code)
            break
        except TimeoutException:
            continue

    # Submit
    for locator in [
        (By.CSS_SELECTOR, "button[type='submit']"),
        (By.CSS_SELECTOR, "input[type='submit']"),
        (By.XPATH, "//button[contains(., 'Log In')]"),
        (By.XPATH, "//button[contains(., 'Log in')]"),
        (By.XPATH, "//button[contains(., 'Continue')]"),
    ]:
        try:
            wait_click(driver, locator)
            break
        except TimeoutException:
            continue

    # Handle Spotify consent/authorization if it appears
    for text in ["agree", "accept", "allow", "authorize"]:
        try:
            wait_click(
                driver,
                (
                    By.XPATH,
                    f"//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
                    f"'abcdefghijklmnopqrstuvwxyz'), '{text}')]",
                ),
            )
            break
        except TimeoutException:
            continue

    # Wait for redirect back to Music League
    WebDriverWait(driver, 45).until(
        lambda d: "app.musicleague.com" in d.current_url.lower() or "musicleague" in d.current_url.lower()
    )
    time.sleep(3)

    return driver


def main():
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    config = load_config(config_path)
    driver = webdriver.Firefox(service=Service(executable_path=config.get("executable_path")))
    try:
        login_to_music_league(driver, config)
        print("Logged in successfully.")
        print(driver.current_url)
    finally:
        # TODO: Set to automatically grab code from email
        # TODO: Access round results
        # TODO: Organize results
        # TODO: Log results to a file
        # TODO: Apply results directly to Google Sheets (?)
        # TODO: Make headless once finished debugging
        driver.quit()


if __name__ == "__main__":
    main()