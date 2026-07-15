"""
WebCrawler.py - Web scraping module for Music League data

This module handles the scraping of Music League round data from the web,
including round information, song submissions, and voting details.

Functions:
    get_round_results(driver, config) - Extracts round data from a single round page
    get_all_rounds(driver, config) - Retrieves all completed rounds from the main page
    check_for_new_rounds(round_number, config) - Checks for and retrieves new rounds
    get_recent_round_number(driver) - Gets the most recent round number
    get_missing_rounds(driver, config, missing_rounds) - Gets specific missing rounds
    get_defunct_players(config) - Retrieves list of defunct players
    get_results(config) - Main function to get all round results
    get_driver(config) - Creates and returns a configured WebDriver instance
"""

import time
import re
import os
from bs4 import BeautifulSoup, NavigableString
from DataCollection.Objects import Round, Voter, Song, convert_username_to_name
from DataCollection.SheetManager import get_defunct_players as gdp
from DataCollection.ExportManager import export_rounds
from DataCollection.LoginManager import login, use_previous_login
from DataCollection.JSONManager import *

def get_round_results(driver, config):
    """
    Extract round information from a single round page.
    
    Args:
        driver: Selenium WebDriver instance
        config: Configuration dictionary
        
    Returns:
        Round object containing round information and submissions
    """
    # Get active and defunct players for name conversion
    active_players = config.get("username-player_name")
    defunct_players = get_defunct_players(config)
    
    try:
        # Parse the page source with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        # Remove empty text nodes to clean up the soup
        for element in soup.find_all(text=True):
            if isinstance(element, NavigableString) and element.strip() == "":
                element.extract()
        
        # Find the round card containing round information
        round_card = soup.find_all(class_="card")[5]
        round_number = int(round_card.find("span").get_text().split()[1])
        title = round_card.find("h5").get_text()
        description = round_card.find("p").get_text()
        
    except Exception as e:
        print(f"Error getting round information: {e}")
        print("Can't get round information")
        return None
    
    # Find all song submission divs
    divs = soup.select("[id*='spotify']")
    submissions = []
    
    for div in divs:
        try:
            # Extract song information
            song_card = div.select_one("div:nth-child(1) > div:nth-child(1) > div:nth-child(2)")
            votes = int(div.select_one("div:nth-child(1) > div:nth-child(1) > div:nth-child(3) > h3").get_text().strip())
            song_name = song_card.find().get_text().strip()
            
            # Get username and convert to player name
            username_div = div.select_one("div[class*='rank-'] > :first-child > :first-child > :last-child > h6")
            player_name = convert_username_to_name(
                active_players=active_players,
                defunct_players=defunct_players,
                name=song_name,
                username=username_div.get_text().strip()
            )
            
            # Extract artist and album
            artist = song_card.select_one(":nth-child(2)").get_text().strip()
            album = song_card.select_one(":nth-child(3)").get_text().strip()
            
            # Process voters
            voters = []
            voters_card = div.select("[id*='votes'] > *")
            
            for voter_info in voters_card:
                voter_name = convert_username_to_name(
                    active_players=active_players,
                    username=voter_info.select_one(":nth-child(2) > b").get_text()
                )
                
                # Get vote count
                vote_block = voter_info.select_one(":nth-child(3) > h6")
                votes_total = int(vote_block.get_text().split()[0]) if vote_block else 0
                
                # Get comment if exists
                comment = ""
                if voter_info.find("span"):
                    comment = voter_info.select_one(":nth-child(2) > span").get_text()
                
                voters.append(Voter(voter_name, votes_total, comment))
            
            # Create song object and add to submissions
            submissions.append(Song(
                player_name=player_name,
                name=song_name,
                artist=artist,
                album=album,
                voters=voters,
                votes=votes
            ))
            
        except Exception as e:
            print(f"Error processing submission: {e}")
            print(f"Can't get submission information: p:{player_name}, s:{song_name}, ar:{artist}, al:{album}, vn: {voter_name}, vt: {votes_total}")
            # Continue processing other submissions instead of failing completely
    
    return Round(title=title, round_number=round_number, description=description, submissions=submissions)

def get_all_rounds(driver, config):
    """
    Retrieve all completed rounds from the main page.
    
    Args:
        driver: Selenium WebDriver instance
        config: Configuration dictionary
        
    Returns:
        List of Round objects sorted by round number
    """
    rounds = []
    time.sleep(2)
    
    # Parse the main page
    soup = BeautifulSoup(driver.page_source, "html.parser")
    
    # Find all completed rounds using status pattern
    status_pattern = re.compile(r"status:\s*'COMPLETE'")
    elems = soup.find_all(
        lambda tag: tag.name == 'div' and 
        tag.has_attr('x-data') and 
        status_pattern.search(tag['x-data'])
    )
    
    # Extract links to each round
    links = []
    for elem in elems:
        anchors = [anchor.get('href') for anchor in elem.find_all("a", href=True)]
        if len(anchors) >= 3:  # Ensure we have enough anchors
            links.append(f"https://app.musicleague.com{anchors[2]}")
    
    # Visit each round link and extract data
    for link in links:
        driver.get(link)
        time.sleep(1)
        round = get_round_results(driver, config)
        if round:  # Only append if round was successfully extracted
            rounds.append(round)
    
    # Sort rounds by round number
    rounds.sort(key=lambda x: (x.round_number))
    return rounds

def check_for_new_rounds(round_number, config):
    """
    Check for and retrieve new rounds since the last known round.
    
    Args:
        round_number: The last known round number
        config: Configuration dictionary
        
    Returns:
        Boolean indicating if new rounds were retrieved
    """
    driver = get_driver(config)
    if not driver:
        driver = login(driver, config)
    
    if not driver:
        print("Failed to get driver")
        return False
    
    # Get the rounds list page
    rounds_list = driver.current_url
    recent_round = get_recent_round_number(driver)
    missing_rounds = recent_round - round_number
    
    if missing_rounds > 0:
        driver.get(rounds_list)
        print(f"Getting information for {missing_rounds} rounds")
        rounds = get_missing_rounds(driver, config, missing_rounds)
        rounds = export_rounds(rounds)
        return bool(rounds)
    else:
        print("No new rounds")
        return False

def get_recent_round_number(driver):
    """
    Get the most recent round number from the current page.
    
    Args:
        driver: Selenium WebDriver instance
        
    Returns:
        Integer representing the most recent round number
    """
    round_number = 0
    time.sleep(2)
    
    try:
        # Parse the page
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        # Find the most recent completed round
        status_pattern = re.compile(r"status:\s*'COMPLETE'")
        elem = soup.find('div', attrs={'x-data': status_pattern})
        
        if elem:
            anchors = [anchor.get('href') for anchor in elem.find_all("a", href=True)]
            if len(anchors) >= 3:
                link = f"https://app.musicleague.com{anchors[2]}"
                driver.get(link)
                time.sleep(1)
                
                # Parse the round page to get round number
                soup = BeautifulSoup(driver.page_source, "html.parser")
                
                # Remove empty text nodes
                for element in soup.find_all(text=True):
                    if isinstance(element, NavigableString) and element.strip() == "":
                        element.extract()
                
                # Find round card and extract number
                round_card = soup.find_all(class_="card")[5]
                round_number = int(round_card.find("span").get_text().split()[1])
                
    except Exception as e:
        print(f"Error getting recent round number: {e}")
    
    return round_number

def get_missing_rounds(driver, config, missing_rounds):
    """
    Get specific missing rounds from the main page.
    
    Args:
        driver: Selenium WebDriver instance
        config: Configuration dictionary
        missing_rounds: Number of missing rounds to retrieve
        
    Returns:
        List of round dictionaries
    """
    # Read existing rounds
    rounds = read_json("rounds")
    time.sleep(5)
    
    # Parse the main page
    soup = BeautifulSoup(driver.page_source, "html.parser")
    
    # Find all completed rounds
    status_pattern = re.compile(r"status:\s*'COMPLETE'")
    elems = soup.find_all(
        lambda tag: tag.name == 'div' and 
        tag.has_attr('x-data') and 
        status_pattern.search(tag['x-data'])
    )
    
    # Extract links for missing rounds
    links = []
    for i in range(min(missing_rounds, len(elems))):  # Prevent index out of bounds
        anchors = [anchor.get('href') for anchor in elems[i].find_all("a", href=True)]
        if len(anchors) >= 3:
            links.append(f"https://app.musicleague.com{anchors[2]}")
    
    # Visit each missing round link and extract data
    for link in links:
        driver.get(link)
        time.sleep(1)
        round = get_round_results(driver, config)
        if round:
            rounds.append(round.__dict__)
    
    # Sort rounds by round number
    rounds.sort(key=lambda x: (x["round_number"]))
    return rounds

def get_defunct_players(config):
    """
    Get the list of defunct players, reading from cache or fetching from the source.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        List of defunct players
    """
    players = read_json("defunct_players")
    if not players:
        players = gdp(config)
        write_json("defunct_players")  # Note: This function might not be properly implemented
    return players

def get_results(config):
    """
    Main function to retrieve all round results.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Exported rounds data or None if failed
    """
    driver = get_driver(config)
    if not driver:
        driver = login(driver, config)
    
    if driver:
        rounds = get_all_rounds(driver, config)
        results = export_rounds(rounds)
        driver.quit()
        return results
    print("Couldn't get results")
    return None

def get_driver(config):
    """
    Create and configure a Selenium WebDriver instance.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Selenium WebDriver instance
    """
    # Get profile path from config
    profile_src = config.get("ffx_profile_path")
    machine_type = os.environ.get("COMPUTER_TYPE", "desktop")
    
    # Adjust profile path based on machine type
    if machine_type == "laptop":
        profile_src += config.get("laptop_profile")
    else:
        profile_src += config.get("desktop_profile")
    
    # Get driver using existing session or create new
    driver = use_previous_login(profile_src, config)
    return driver
"""
WebCrawler.py - Web scraping module for Music League data

This module handles the scraping of Music League round data from the web,
including round information, song submissions, and voting details.

Functions:
    get_round_results(driver, config) - Extracts round data from a single round page
    get_all_rounds(driver, config) - Retrieves all completed rounds from the main page
    check_for_new_rounds(round_number, config) - Checks for and retrieves new rounds
    get_recent_round_number(driver) - Gets the most recent round number
    get_missing_rounds(driver, config, missing_rounds) - Gets specific missing rounds
    get_defunct_players(config) - Retrieves list of defunct players
    get_results(config) - Main function to get all round results
    get_driver(config) - Creates and returns a configured WebDriver instance
"""

import time
import re
import os
from bs4 import BeautifulSoup, NavigableString
from DataCollection.Objects import Round, Voter, Song, convert_username_to_name
from DataCollection.SheetManager import get_defunct_players as gdp
from DataCollection.ExportManager import export_rounds
from DataCollection.LoginManager import login, use_previous_login
from DataCollection.JSONManager import *

def get_round_results(driver, config):
    """
    Extract round information from a single round page.
    
    Args:
        driver: Selenium WebDriver instance
        config: Configuration dictionary
        
    Returns:
        Round object containing round information and submissions
    """
    # Get active and defunct players for name conversion
    active_players = config.get("username-player_name")
    defunct_players = get_defunct_players(config)
    
    try:
        # Parse the page source with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        # Remove empty text nodes to clean up the soup
        for element in soup.find_all(text=True):
            if isinstance(element, NavigableString) and element.strip() == "":
                element.extract()
        
        # Find the round card containing round information
        round_card = soup.find_all(class_="card")[5]
        round_number = int(round_card.find("span").get_text().split()[1])
        title = round_card.find("h5").get_text()
        description = round_card.find("p").get_text()
        
    except Exception as e:
        print(f"Error getting round information: {e}")
        print("Can't get round information")
        return None
    
    # Find all song submission divs
    divs = soup.select("[id*='spotify']")
    submissions = []
    
    for div in divs:
        try:
            # Extract song information
            song_card = div.select_one("div:nth-child(1) > div:nth-child(1) > div:nth-child(2)")
            votes = int(div.select_one("div:nth-child(1) > div:nth-child(1) > div:nth-child(3) > h3").get_text().strip())
            song_name = song_card.find().get_text().strip()
            
            # Get username and convert to player name
            username_div = div.select_one("div[class*='rank-'] > :first-child > :first-child > :last-child > h6")
            player_name = convert_username_to_name(
                active_players=active_players,
                defunct_players=defunct_players,
                name=song_name,
                username=username_div.get_text().strip()
            )
            
            # Extract artist and album
            artist = song_card.select_one(":nth-child(2)").get_text().strip()
            album = song_card.select_one(":nth-child(3)").get_text().strip()
            
            # Process voters
            voters = []
            voters_card = div.select("[id*='votes'] > *")
            
            for voter_info in voters_card:
                voter_name = convert_username_to_name(
                    active_players=active_players,
                    username=voter_info.select_one(":nth-child(2) > b").get_text()
                )
                
                # Get vote count
                vote_block = voter_info.select_one(":nth-child(3) > h6")
                votes_total = int(vote_block.get_text().split()[0]) if vote_block else 0
                
                # Get comment if exists
                comment = ""
                if voter_info.find("span"):
                    comment = voter_info.select_one(":nth-child(2) > span").get_text()
                
                voters.append(Voter(voter_name, votes_total, comment))
            
            # Create song object and add to submissions
            submissions.append(Song(
                player_name=player_name,
                name=song_name,
                artist=artist,
                album=album,
                voters=voters,
                votes=votes
            ))
            
        except Exception as e:
            print(f"Error processing submission: {e}")
            print(f"Can't get submission information: p:{player_name}, s:{song_name}, ar:{artist}, al:{album}, vn: {voter_name}, vt: {votes_total}")
            # Continue processing other submissions instead of failing completely
    
    return Round(title=title, round_number=round_number, description=description, submissions=submissions)

def get_all_rounds(driver, config):
    """
    Retrieve all completed rounds from the main page.
    
    Args:
        driver: Selenium WebDriver instance
        config: Configuration dictionary
        
    Returns:
        List of Round objects sorted by round number
    """
    rounds = []
    time.sleep(2)
    
    # Parse the main page
    soup = BeautifulSoup(driver.page_source, "html.parser")
    
    # Find all completed rounds using status pattern
    status_pattern = re.compile(r"status:\s*'COMPLETE'")
    elems = soup.find_all(
        lambda tag: tag.name == 'div' and 
        tag.has_attr('x-data') and 
        status_pattern.search(tag['x-data'])
    )
    
    # Extract links to each round
    links = []
    for elem in elems:
        anchors = [anchor.get('href') for anchor in elem.find_all("a", href=True)]
        if len(anchors) >= 3:  # Ensure we have enough anchors
            links.append(f"https://app.musicleague.com{anchors[2]}")
    
    # Visit each round link and extract data
    for link in links:
        driver.get(link)
        time.sleep(1)
        round = get_round_results(driver, config)
        if round:  # Only append if round was successfully extracted
            rounds.append(round)
    
    # Sort rounds by round number
    rounds.sort(key=lambda x: (x.round_number))
    return rounds

def check_for_new_rounds(round_number, config):
    """
    Check for and retrieve new rounds since the last known round.
    
    Args:
        round_number: The last known round number
        config: Configuration dictionary
        
    Returns:
        Boolean indicating if new rounds were retrieved
    """
    driver = get_driver(config)
    if not driver:
        driver = login(driver, config)
    
    if not driver:
        print("Failed to get driver")
        return False
    
    # Get the rounds list page
    rounds_list = driver.current_url
    recent_round = get_recent_round_number(driver)
    missing_rounds = recent_round - round_number
    
    if missing_rounds > 0:
        driver.get(rounds_list)
        print(f"Getting information for {missing_rounds} rounds")
        rounds = get_missing_rounds(driver, config, missing_rounds)
        rounds = export_rounds(rounds)
        return bool(rounds)
    else:
        print("No new rounds")
        return False

def get_recent_round_number(driver):
    """
    Get the most recent round number from the current page.
    
    Args:
        driver: Selenium WebDriver instance
        
    Returns:
        Integer representing the most recent round number
    """
    round_number = 0
    time.sleep(2)
    
    try:
        # Parse the page
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        # Find the most recent completed round
        status_pattern = re.compile(r"status:\s*'COMPLETE'")
        elem = soup.find('div', attrs={'x-data': status_pattern})
        
        if elem:
            anchors = [anchor.get('href') for anchor in elem.find_all("a", href=True)]
            if len(anchors) >= 3:
                link = f"https://app.musicleague.com{anchors[2]}"
                driver.get(link)
                time.sleep(1)
                
                # Parse the round page to get round number
                soup = BeautifulSoup(driver.page_source, "html.parser")
                
                # Remove empty text nodes
                for element in soup.find_all(text=True):
                    if isinstance(element, NavigableString) and element.strip() == "":
                        element.extract()
                
                # Find round card and extract number
                round_card = soup.find_all(class_="card")[5]
                round_number = int(round_card.find("span").get_text().split()[1])
                
    except Exception as e:
        print(f"Error getting recent round number: {e}")
    
    return round_number

def get_missing_rounds(driver, config, missing_rounds):
    """
    Get specific missing rounds from the main page.
    
    Args:
        driver: Selenium WebDriver instance
        config: Configuration dictionary
        missing_rounds: Number of missing rounds to retrieve
        
    Returns:
        List of round dictionaries
    """
    # Read existing rounds
    rounds = read_json("rounds")
    time.sleep(5)
    
    # Parse the main page
    soup = BeautifulSoup(driver.page_source, "html.parser")
    
    # Find all completed rounds
    status_pattern = re.compile(r"status:\s*'COMPLETE'")
    elems = soup.find_all(
        lambda tag: tag.name == 'div' and 
        tag.has_attr('x-data') and 
        status_pattern.search(tag['x-data'])
    )
    
    # Extract links for missing rounds
    links = []
    for i in range(min(missing_rounds, len(elems))):  # Prevent index out of bounds
        anchors = [anchor.get('href') for anchor in elems[i].find_all("a", href=True)]
        if len(anchors) >= 3:
            links.append(f"https://app.musicleague.com{anchors[2]}")
    
    # Visit each missing round link and extract data
    for link in links:
        driver.get(link)
        time.sleep(1)
        round = get_round_results(driver, config)
        if round:
            rounds.append(round.__dict__)
    
    # Sort rounds by round number
    rounds.sort(key=lambda x: (x["round_number"]))
    return rounds

def get_defunct_players(config):
    """
    Get the list of defunct players, reading from cache or fetching from the source.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        List of defunct players
    """
    players = read_json("defunct_players")
    if not players:
        players = gdp(config)
        write_json("defunct_players")  # Note: This function might not be properly implemented
    return players

def get_results(config):
    """
    Main function to retrieve all round results.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Exported rounds data or None if failed
    """
    driver = get_driver(config)
    if not driver:
        driver = login(driver, config)
    
    if driver:
        rounds = get_all_rounds(driver, config)
        results = export_rounds(rounds)
        driver.quit()
        return results
    print("Couldn't get results")
    return None

def get_driver(config):
    """
    Create and configure a Selenium WebDriver instance.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Selenium WebDriver instance
    """
    # Get profile path from config
    profile_src = config.get("ffx_profile_path")
    machine_type = os.environ.get("COMPUTER_TYPE", "desktop")
    
    # Adjust profile path based on machine type
    if machine_type == "laptop":
        profile_src += config.get("laptop_profile")
    else:
        profile_src += config.get("desktop_profile")
    
    # Get driver using existing session or create new
    driver = use_previous_login(profile_src, config)
    return driver