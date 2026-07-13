import time, re, os
from bs4 import BeautifulSoup, NavigableString
from Objects import Round, Voter, Song, convert_username_to_name
from SheetManager import get_defunct_players as gdp
from ExportManager import export_rounds
from LoginManager import login, use_previous_login
from JSONManager import *

def get_round_results(driver, config):
    active_players = config.get("username-player_name")
    defunct_players = get_defunct_players(config)
    try:
        soup = BeautifulSoup(driver.page_source, "html.parser")
        for element in soup.find_all(text=True):
            if isinstance(element, NavigableString) and element.strip() == "":
                element.extract()
        round_card = soup.find_all(class_= "card")[5]
        round_number = int(round_card.find("span").get_text().split()[1])
        title = round_card.find("h5").get_text()
        description = round_card.find("p").get_text()
    except Exception as e:
        print(e)
        print("Can't get round information")    
    divs = soup.select("[id*='spotify']")
    submissions = []
    for div in divs:
        try:
            song_card = div.select_one("div:nth-child(1) > div:nth-child(1) > div:nth-child(2)")
            votes = int(div.select_one("div:nth-child(1) > div:nth-child(1) > div:nth-child(3) > h3").get_text().strip())
            song_name = song_card.find().get_text().strip()
            username_div = div.select_one("div[class*='rank-'] > :first-child > :first-child > :last-child > h6")
            player_name = convert_username_to_name(active_players = active_players, defunct_players = defunct_players, name = song_name, username = username_div.get_text().strip())
            artist = song_card.select_one(":nth-child(2)").get_text().strip()
            album = song_card.select_one(":nth-child(3)").get_text().strip()
            voters=[]
            voters_card = div.select("[id*='votes'] > *")
            for voter_info in voters_card:
                voter_name = convert_username_to_name(active_players = active_players, username = voter_info.select_one(":nth-child(2) > b").get_text())
                vote_block = voter_info.select_one(":nth-child(3) > h6")
                if vote_block:
                    votes_total = int(vote_block.get_text().split()[0])
                else:
                    votes_total = 0
                comment = ""
                if voter_info.find("span"):
                    comment = voter_info.select_one(":nth-child(2) > span").get_text()
                voters.append(Voter(voter_name, votes_total, comment))
            submissions.append(Song(player_name=player_name, name=song_name, artist=artist, album=album, voters=voters, votes=votes))
        except Exception as e:
                print(e)
                print(f"Can't get submission information: p:{player_name}, s:{song_name}, ar:{artist}, al:{album}, vn: {voter_name}, vt: {votes_total}")
    return Round(title=title, round_number=round_number, description=description, submissions=submissions)

def get_all_rounds(driver, config):
    rounds = []
    time.sleep(2)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    status_pattern = re.compile(r"status:\s*'COMPLETE'")
    elems = soup.find_all(
        lambda tag: tag.name == 'div' and 
        tag.has_attr('x-data') and 
        status_pattern.search(tag['x-data']))
    links = []
    for elem in elems:
        anchors = [anchor.get('href') for anchor in elem.find_all("a", href = True)]
        links.append(f"https://app.musicleague.com{anchors[2]}")
    for link in links:
        driver.get(link)
        time.sleep(1)
        round = get_round_results(driver, config)
        rounds.append(round)
    rounds.sort(key = lambda x: (x.round_number))
    return rounds 

def check_for_new_rounds(round_number, config):
    driver = get_driver(config)
    if not driver:
        login(driver, config)
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
    round_number = 0
    time.sleep(2)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    status_pattern = re.compile(r"status:\s*'COMPLETE'")
    elem = soup.find('div', attrs = {'x-data': status_pattern})
    anchors = [anchor.get('href') for anchor in elem.find_all("a", href = True)]
    link = (f"https://app.musicleague.com{anchors[2]}")
    driver.get(link)
    time.sleep(1)
    try:
        soup = BeautifulSoup(driver.page_source, "html.parser")
        for element in soup.find_all(text=True):
            if isinstance(element, NavigableString) and element.strip() == "":
                element.extract()
        round_card = soup.find_all(class_= "card")[5]
        round_number = int(round_card.find("span").get_text().split()[1])
    except Exception as e:
        print(e)
    return round_number

def get_missing_rounds(driver, config, missing_rounds):  
    rounds = read_json("rounds")
    time.sleep(5)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    status_pattern = re.compile(r"status:\s*'COMPLETE'")
    elems = soup.find_all(
        lambda tag: tag.name == 'div' and 
        tag.has_attr('x-data') and 
        status_pattern.search(tag['x-data']))
    links = []
    for i in range(missing_rounds):
        anchors = [anchor.get('href') for anchor in elems[i].find_all("a", href = True)]
        links.append(f"https://app.musicleague.com{anchors[2]}")
    for link in links:
        driver.get(link)
        time.sleep(1)
        round = get_round_results(driver, config)
        rounds.append(round.__dict__)
    rounds.sort(key = lambda x: (x["round_number"]))
    return rounds

def get_defunct_players(config):
    players = []
    players = read_json("defunct_players")
    if not players:
        players = gdp(config)
        write_json("defunct_players")
    return players
    

def get_results(config):
    driver = get_driver(config)
    if not driver:
        driver = login(driver, config)
    if driver:
        rounds = get_all_rounds(driver, config)
        results = export_rounds(rounds)
        driver.quit()
        return results
    print("Couldn't get results")

def get_driver(config):
    profile_src = config.get("ffx_profile_path")
    machine_type = os.environ.get("COMPUTER_TYPE", "desktop")
    if machine_type  == "laptop":
        profile_src += config.get("laptop_profile")
    else:
        profile_src += config.get("desktop_profile")
    driver = use_previous_login(profile_src, config)
    return driver
    