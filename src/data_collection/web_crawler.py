"""
web_crawler.py - Web scraping module for Music League data

This module handles the scraping of Music League round data from the web,
including round information, song submissions, and voting details.
"""

import time
import re
import os
import glob
import sys
from bs4 import BeautifulSoup, NavigableString
from data_collection.objects import Round, Voter, Song, convert_username_to_name
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile

_global_avatar_cache = {}

def load_avatar_cache(database_avatars: dict):
    """Called by your pipeline step to synchronize your Postgres records with runtime memory."""
    global _global_avatar_cache
    _global_avatar_cache = database_avatars if database_avatars else {}

def get_avatar_cache() -> dict:
    """Returns the updated avatar records to be written into the Postgres JSONB schema."""
    global _global_avatar_cache
    return _global_avatar_cache

def get_avatar_url(div, player_name):
    """
    Extracts avatar image URL and updates an in-memory cache dictionary 
    instead of calling disk-bound write_json().
    """
    global _global_avatar_cache
    try:
        avatar_img = div.select_one("div[class*='rank-'] > :first-child > :first-child > :nth-child(2) > img")
        if not avatar_img:
            return
            
        avatar_url = avatar_img.get("src")
        _global_avatar_cache[player_name] = avatar_url
    except Exception as e:
        print(f"Failed parsing avatar for player {player_name}: {e}")

def get_round_results(driver, config):
    """
    Extract round information from a single round page.
    """
    players = config.get("username-player_name")
    try:
        soup = BeautifulSoup(driver.page_source, "html.parser")
        for element in soup.find_all(string=True):
            if isinstance(element, NavigableString) and element.strip() == "":
                element.extract()
        
        round_card = soup.find_all(class_="card")[5]
        round_number = int(round_card.find("span").get_text().split()[1])
        title = round_card.find("h5").get_text()
        description = round_card.find("p").get_text()
        
    except Exception as e:
        print(f"Error getting round information: {e}")
        return None
    
    divs = soup.select("[id*='spotify']")
    submissions = []
    
    for div in divs:
        try:
            song_card = div.select_one("div:nth-child(1) > div:nth-child(1) > div:nth-child(2)")
            votes = int(div.select_one("div:nth-child(1) > div:nth-child(1) > div:nth-child(3) > h3").get_text().strip())
            song_name = song_card.find().get_text().strip()
            
            username_div = div.select_one("div[class*='rank-'] > :first-child > :first-child > :last-child > h6")
            user_comment = div.select_one("div:nth-child(2) > p > span").get_text().strip()
            player_name = convert_username_to_name(
                username=username_div.get_text().strip(),
                players=players
            )
        
            get_avatar_url(div, player_name)
            
            artist = song_card.select_one(":nth-child(2)").get_text().strip()
            album = song_card.select_one(":nth-child(3)").get_text().strip()
            
            voters = []
            voters_card = div.select("[id*='votes'] > *")
            
            for voter_info in voters_card:
                voter_name = convert_username_to_name(
                    username=voter_info.select_one(":nth-child(2) > b").get_text(),
                    players=players
                )
                
                vote_block = voter_info.select_one(":nth-child(3) > h6")
                votes_total = int(vote_block.get_text().split()[0]) if vote_block else 0
                
                comment = ""
                if voter_info.find("span"):
                    comment = voter_info.select_one(":nth-child(2) > span").get_text()
                
                voters.append(Voter(voter_name, votes_total, comment))
            
            submissions.append(Song(
                name=song_name,
                votes=votes,
                player_name=player_name,
                artist=artist,
                album=album,
                user_comment = user_comment,
                voters=voters
            ))
            
        except Exception as e:
            print(f"Error processing submission: {e}")
    
    return Round(title=title, round_number=round_number, description=description, submissions=submissions)

def get_all_rounds(driver, config):
    """
    Retrieve all completed rounds from the main page.
    """
    rounds = []
    
    soup = BeautifulSoup(driver.page_source, "html.parser")
    status_pattern = re.compile(r"status:\s*'COMPLETE'")
    elems = soup.find_all(
        lambda tag: tag.name == 'div' and 
        tag.has_attr('x-data') and 
        status_pattern.search(tag['x-data'])
    )
    
    links = []
    for elem in elems:
        anchors = [anchor.get('href') for anchor in elem.find_all("a", href=True)]
        if len(anchors) >= 3:
            links.append(f"https://app.musicleague.com{anchors[2]}")
    print("Round links found")
    i = 1
    for link in links:
        print(f"Round {i} of {links.__len__()}")
        driver.get(link)
        time.sleep(1)
        round_data = get_round_results(driver, config)
        if round_data:
            rounds.append(round_data)
        i += 1
            
    if isinstance(rounds, dict):
        rounds.sort(key=lambda x: x["round_number"])
    else:
        rounds.sort(key=lambda x: x.round_number)
    print("Got all rounds")
    return rounds

def check_for_new_rounds(driver, config, results=None):
    """
    Check for and retrieve new rounds since the last known round in the database.
    """
    round_number = int(results[-1]["round_number"] if isinstance(results[-1], dict) else results[-1].round_number)
    try:
        rounds_list = driver.current_url
        recent_round = get_recent_round_number(driver)
        missing_rounds = recent_round - round_number
        
        if missing_rounds > 0:
            driver.get(rounds_list)
            print(f"Getting information for {missing_rounds} missing rounds")
            updated_rounds = get_missing_rounds(driver, config, missing_rounds, results)
            return updated_rounds
        else:
            print("No new rounds detected.")
            return results
    finally:
        driver.quit()

def get_recent_round_number(driver):
    """
    Get the most recent round number from the current page.
    """
    round_number = 0
    time.sleep(2)
    try:
        soup = BeautifulSoup(driver.page_source, "html.parser")
        status_pattern = re.compile(r"status:\s*'COMPLETE'")
        elem = soup.find('div', attrs={'x-data': status_pattern})
        
        if elem:
            anchors = [anchor.get('href') for anchor in elem.find_all("a", href=True)]
            if len(anchors) >= 3:
                link = f"https://app.musicleague.com{anchors[2]}"
                driver.get(link)
                time.sleep(1)
                
                soup = BeautifulSoup(driver.page_source, "html.parser")
                for element in soup.find_all(string=True):
                    if isinstance(element, NavigableString) and element.strip() == "":
                        element.extract()
                
                round_card = soup.find_all(class_="card")[5]
                round_number = int(round_card.find("span").get_text().split()[1])
    except Exception as e:
        print(f"Error getting recent round number: {e}")
    return round_number

def get_missing_rounds(driver, config, missing_rounds, existing_rounds_cache):
    """
    Get specific missing rounds using state arrays injected from Postgres.
    """
    rounds = existing_rounds_cache if existing_rounds_cache else []
    if rounds[0].get("round_number") == 0:
        rounds = []
    time.sleep(5)
    
    soup = BeautifulSoup(driver.page_source, "html.parser")
    status_pattern = re.compile(r"status:\s*'COMPLETE'")
    elems = soup.find_all(
        lambda tag: tag.name == 'div' and 
        tag.has_attr('x-data') and 
        status_pattern.search(tag['x-data'])
    )
    
    links = []
    for i in range(min(missing_rounds, len(elems))):
        anchors = [anchor.get('href') for anchor in elems[i].find_all("a", href=True)]
        if len(anchors) >= 3:
            links.append(f"https://app.musicleague.com{anchors[2]}")
            
    for link in links:
        driver.get(link)
        time.sleep(1)
        round_data = get_round_results(driver, config)
        if round_data:
            rounds.append(round_data)
            print(f"Got round {links.__len__() - round_data.round_number + 1} out of {links.__len__()}")
    return rounds

def get_firefox_profile_path():
    home = os.path.expanduser("~")

    if os.name == "nt":
        base_path = os.path.join(home, "AppData", "Roaming", "Mozilla", "Firefox", "Profiles")
    elif sys.platform == "darwin":
        base_path = os.path.join(home, "Library", "Application Support", "Mozilla", "Firefox", "Profiles")
    else:
        base_path = os.path.join(home, ".mozilla", "firefox")

    profiles = glob.glob(os.path.join(base_path, "*.default*"))
    if not profiles:
        raise FileNotFoundError("No Firefox profile found. Please ensure Firefox is installed.")

    return profiles[0]

def get_chrome_user_data_dir():
    home = os.path.expanduser("~")

    if os.name == "nt":
        return os.path.join(home, "AppData", "Local", "Google", "Chrome", "User Data")
    elif sys.platform == "darwin":
        return os.path.join(home, "Library", "Application Support", "Google", "Chrome")
    else:
        return os.path.join(home, ".config", "google-chrome")

def setup_authenticated_driver(config: dict):
    """
    Initializes a headless driver container and injects the dynamic cookie jar
    across all musicleague subdomains before data collection queries trigger.
    """
    browser_type = config.get("browser_type", "chromium")
    if browser_type == "firefox":
        try:
            profile_path = get_firefox_profile_path()
            safe_profile = FirefoxProfile(profile_path)
            options = FirefoxOptions()
            options.add_argument("-headless")
            options.profile = safe_profile
        except Exception:
            options = FirefoxOptions()
            
        driver = webdriver.Firefox(options=options)
    else:
        user_data_path = get_chrome_user_data_dir()
        options = ChromeOptions()
        
        options.add_argument(f"--user-data-dir={user_data_path}-selenium-test")
        options.add_argument("--headless")
        options.add_argument("--profile-directory=Default")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        
        driver = webdriver.Chrome(options=options)

    if driver is None:
        print("Driver failed")
    else:
        print("Driver Authenticated")
    time.sleep(1)
    return driver
        
def get_results(config, results = None):
    if results is None:
        results = []
    driver = None
    try:
        driver = setup_authenticated_driver(config)
        if not driver:
                print("Aborting collection pipeline run: Driver failed authentication allocation.")
                return results
        target_url = f"https://app.musicleague.com/l/{config.get('league_id')}/"
        driver.get(target_url)
        time.sleep(1)
        if results:
            return check_for_new_rounds(driver, config, results=results)
        else:
            return get_all_rounds(driver, config)     
    except Exception as e:
        print(f"Critical execution error in get_results block: {e}")
        return results
        
    finally:
        if driver is not None:
            try:
                driver.quit()
            except Exception as e:
                print(f"Error closing webdriver: {e}")