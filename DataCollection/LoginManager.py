from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium import webdriver
import imaplib, email, shutil, time, re, os

# Global variable to store the Spotify authorization code
code = ""

def wait_click(driver, locator, timeout=10):
    """
    Wait for an element to be clickable and then click it.
    
    Args:
        driver: Selenium WebDriver instance
        locator: Tuple of (By, locator_value) for the element
        timeout (int): Maximum time to wait for element (default: 10 seconds)
        
    Returns:
        None
    """
    WebDriverWait(driver, timeout).until(EC.element_to_be_clickable(locator)).click()

def fill_email(driver, locator, value, timeout=10):
    """
    Wait for an email input field to be visible and fill it with the provided value.
    
    Args:
        driver: Selenium WebDriver instance
        locator: Tuple of (By, locator_value) for the email input field
        value (str): Email address to fill in
        timeout (int): Maximum time to wait for element (default: 10 seconds)
        
    Returns:
        None
    """
    elem = WebDriverWait(driver, timeout).until(EC.visibility_of_element_located(locator))
    elem.send_keys(value)

def fill_code(driver, locator, value, timeout=60):
    """
    Fill a 6-digit authorization code into individual input fields.
    
    Args:
        driver: Selenium WebDriver instance
        locator: Tuple of (By, locator_value) for the code input fields
        value (str): 6-digit authorization code
        timeout (int): Maximum time to wait for elements (default: 60 seconds)
        
    Returns:
        None
    """
    elems = WebDriverWait(driver, timeout).until(EC.visibility_of_all_elements_located(locator))
    for elem, digit in zip(elems, value):
        elem.send_keys(digit)

def click_by_text(driver, texts, timeout=10):
    """
    Click on an element by searching for text within buttons, links, or inputs.
    
    Args:
        driver: Selenium WebDriver instance
        texts (list): List of text strings to search for
        timeout (int): Maximum time to wait for element (default: 10 seconds)
        
    Returns:
        bool: True if an element was clicked, False otherwise
    """
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
    """
    Retrieve the 6-digit authorization code from Spotify's email.
    
    Args:
        config (dict): Configuration dictionary containing email and password
        
    Returns:
        str: 6-digit authorization code or empty string if not found
    """
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    time.sleep(15)
    mail.login(config.get("email"), config.get("password"))
    mail.select("inbox", readonly=False)
    
    # Wait for Spotify email to arrive
    waiting = True
    while waiting:
        status, messages = mail.search(None, '(FROM "Spotify")')   
        if status != 'OK' or not messages[0]:
            print("Email not found")
        else:
            break   
            
    # Get the most recent email
    email_id = messages[0].split()[-1]
    status, data = mail.fetch(email_id, "(RFC822)")
    if status != "OK":
        print("Subject not found")
        return ""
        
    msg = email.message_from_bytes(data[0][1])
    subject, encoding = email.header.decode_header(msg["Subject"])[0]
    if isinstance(subject, bytes):
        subject = subject.decode(encoding or "utf-8")
        
    # Extract 6-digit code from subject
    match = re.search(r"\d{6}", subject)
    global code
    if match:
        code = match.group(0)
        
    # Mark email as deleted and expunge
    if code:        
        mail.store(email_id, "+FLAGS", "\\Deleted")
        mail.expunge()
        
    mail.close()
    mail.logout()
    
    return code

def login(driver, config):
    """
    Perform login to the music league using Spotify authentication.
    
    Args:
        driver: Selenium WebDriver instance (can be None)
        config (dict): Configuration dictionary with required keys:
            - league_url (str): URL of the music league
            - email (str): Spotify email address
            - password (str): Spotify password
            - executable_path (str): Path to geckodriver executable
            
    Returns:
        WebDriver: Selenium WebDriver instance after successful login
        
    Raises:
        ValueError: If email is not provided in config
        RuntimeError: If login fails
    """
    # Create headless Firefox driver
    options = Options()
    options.add_argument("-headless")
    driver = webdriver.Firefox(options=options, service=Service(executable_path=config.get("executable_path")))
    
    # Navigate to league login page
    login_url = config.get("league_url")
    driver.get(login_url)
    time.sleep(2)
    
    # Try to click Spotify login button
    click_by_text(driver, ["spotify"])
    
    # If we haven't navigated to Spotify, try alternative selectors
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
                
    # Validate email configuration
    spotify_username = config.get("email")
    if not spotify_username:
        raise ValueError("Config file must contain email")
        
    # Fill email and continue
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
            
    # Get authorization code and fill it in
    global code
    for locator in [
        (By.CSS_SELECTOR, "input[inputmode='numeric']"),
    ]:
        try:
            # Wait for code to be available
            while code == "":
                get_spotify_code(config)
                
            fill_code(driver, locator, code)
            break
        except TimeoutException:
            continue
            
    # Clear global code variable
    code = ""
    
    # Accept authorization
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
            
    # Wait for successful navigation to league page
    WebDriverWait(driver, 10).until(
        lambda d: "app.musicleague.com" in d.current_url.lower() or "musicleague" in d.current_url.lower()
    )
    time.sleep(3)
    
    return driver

def use_previous_login(profile_src, config):
    """
    Use a previously saved Firefox profile for login.
    
    Args:
        profile_src (str): Path to the source Firefox profile directory
        config (dict): Configuration dictionary with required keys:
            - league_url (str): URL of the music league
            - executable_path (str): Path to geckodriver executable
            
    Returns:
        WebDriver: Selenium WebDriver instance after login or None if failed
    """
    driver = None
    profile_temp = "/tmp/ffx_crawler"
    
    try:
        if profile_src:
            # Clean up existing temp profile
            if os.path.exists(profile_temp):
                try:
                    shutil.rmtree(profile_temp)
                except PermissionError:
                    os.rename(profile_temp, f"{profile_temp}_old_{int(time.time())}")
                    
            # Copy profile with ignore patterns
            ignore_files = shutil.ignore_patterns(
                "lock", ".parentlock", "parent.lock", 
                "sessionstore.jsonlz4", "compatibility.ini"
            )
            shutil.copytree(profile_src, profile_temp, ignore=ignore_files)
            
            # Create Firefox driver with profile
            options = Options()
            options.add_argument("-profile")
            options.add_argument(profile_temp)
            options.add_argument("-headless")
            driver = webdriver.Firefox(options=options, service=Service(executable_path=config.get("executable_path")))
            
            # Navigate to league and refresh
            driver.get(config.get("league_url"))
            time.sleep(3)
            driver.refresh()
            
            # Check if login was successful
            if "invite" in driver.current_url or "login" in driver.current_url:
                raise RuntimeError(f"Previous login failed")
                
        print("Successfully used previous login")
        
    except Exception as e:
        print(f"An error occurred during login: {e}")
        return None
        
    return driver