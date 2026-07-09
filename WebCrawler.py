import time
import imaplib
import email
import re
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from Parser import parse_round_results, parse_submission

code = ""  # Global variable to store the Spotify verification code

def wait_click(driver, locator, timeout=10):
    WebDriverWait(driver, timeout).until(EC.element_to_be_clickable(locator)).click()


def fill_email(driver, locator, value, timeout=10):
    elem = WebDriverWait(driver, timeout).until(EC.visibility_of_element_located(locator))
    elem.send_keys(value)

def fill_code(driver, locator, value, timeout=60):
    elems = WebDriverWait(driver, timeout).until(EC.visibility_of_all_elements_located(locator))
    for elem, digit in zip(elems, value):
        elem.send_keys(digit)

def click_by_text(driver, texts, timeout=10):
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

def get_spotify_code(config):
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    time.sleep(15)
    mail.login(config.get("email"), config.get("password"))
    mail.select("inbox", readonly = False)
    waiting = True
    while waiting:
        status, messages = mail.search(None, '(FROM "Spotify")')
    
        if status != 'OK' or not messages[0]:
            print("Email not found")
        else:
            break
    
    email_id = messages[0].split()[-1]
    status, data = mail.fetch(email_id, "(RFC822)")

    if status != "OK":
        print("Subject not found")
        return
    
    msg = email.message_from_bytes(data[0][1])
    subject, encoding = email.header.decode_header(msg["Subject"])[0]
    if isinstance(subject, bytes):
        subject = subject.decode(encoding or "utf-8")
    match = re.search(r"\d{6}", subject)
    global code
    if match:
        code = match.group(0)
    if code:        
        mail.store(email_id, "+FLAGS", "\\Deleted")
        mail.expunge()
    mail.close()
    mail.logout()
    

def login(driver, config):
    login_url = config.get("league_url")
    driver.get(login_url)

    # Click the Music League login option that redirects to Spotify
    click_by_text(driver, ["spotify"])

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
                print("Can't get to Spotify")
                continue

    # Spotify login page
    spotify_username = config.get("email")
    
    if not spotify_username:
        raise ValueError("Config file must contain email")

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
            print("Can't add email address")
            continue

    global code
    # Fill code
    for locator in [
        (By.CSS_SELECTOR, "input[inputmode='numeric']"),
    ]:
        try:
            while code == "":
                get_spotify_code(config)
            fill_code(driver, locator, code)
            break
        except TimeoutException:
            continue
    
    code = ""

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
            print("Can't authorize login")
            continue

    # Wait for redirect back to Music League
    WebDriverWait(driver, 45).until(
        lambda d: "app.musicleague.com" in d.current_url.lower() or "musicleague" in d.current_url.lower()
    )
    time.sleep(3)

    return driver

def get_round_results(driver):
    rounds = []
    time.sleep(5)
    round_list = driver.current_window_handle
    soup = BeautifulSoup(driver.page_source, "html.parser")
    status_pattern = re.compile(r"status:\s*'COMPLETE'")

    #Get all completed rounds
    elems = soup.find_all(
        lambda tag: tag.name == 'div' and 
        tag.has_attr('x-data') and 
        status_pattern.search(tag['x-data']))
    links = []
    for elem in elems:
        anchors = [anchor.get('href') for anchor in elem.find_all("a", href = True)]
        links.append(f"https://app.musicleague.com{anchors[2]}")
    for link in links:
        # Open each completed round in a new tab to get the results and switch back to round list
        driver.switch_to.new_window('tab')
        driver.get(link)
        time.sleep(2)
        try:
            soup = BeautifulSoup(driver.page_source, "html.parser")
            round_card = soup.find_all(class_= "card")[5]
            round_number = int(round_card.find("span").get_text().split()[1])
            title = round_card.find("h5").get_text()
            description = round_card.find("p").get_text()
        except Exception as e:
            print(e)
            print("Can't get round information")
        
        divs = soup.select("[id*='spotify']")
        results = []
        for div in divs:
            try:
                song_card = div.select_one("div:nth-child(1) > div:nth-child(1) > div:nth-child(2)")
                voters_card = div.select("[id*='votes']")
                player_card = div.select_one("div:nth-child(1) > div:nth-child(2) > div:nth-child(1) > div:nth-child(1) > div:last-child")
                votes = int(div.select_one("div:nth-child(1) > div:nth-child(1) > div:nth-child(3) > h3").get_text().strip())
                results.append(parse_submission(player_card, song_card, voters_card, votes))
            except Exception as e:
                    print(e)
                    print("Can't get result information")
            round = parse_round_results(title, round_number, description, results)
        rounds.append(round)
        driver.switch_to.window(round_list)
    return rounds.sort(key = lambda x: (x.round_number))

def crawl(config):
    driver = webdriver.Firefox(service=Service(executable_path=config.get("executable_path")))
    try:
        login(driver, config)
        results = get_round_results(driver)
        return results
    except Exception as e:
        print(f"An error occurred during login: {e}")
    return