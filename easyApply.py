import subprocess
from time import sleep
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from dotenv import load_dotenv
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import socket
from scrapingQuestions import readTheInputsFrom

load_dotenv()

chromeDriverPath = os.getenv('CHROME_DRIVER_PATH')
chromeAppPath = os.getenv('CHROME_APP_PATH')
chromeUserDataDir = os.getenv('CHROME_USER_DATA_DIR')
debuggingPort = os.getenv('DEBUGGING_PORT')

def isPortInUse(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('localhost', int(port)))
            return False
        except socket.error:
            return True

def startChrome(debuggingPort, userDataDir, chromeAppPath):
    if isPortInUse(debuggingPort):
        print(f"Chrome is already running on port {debuggingPort}, reusing existing instance...")
        return None
    
    print("Starting new Chrome instance...")
    chromeApp = subprocess.Popen([
        chromeAppPath,
        f'--remote-debugging-port={debuggingPort}',
        f'--user-data-dir={userDataDir}'
    ])
    sleep(2)
    return chromeApp

def setupChromeDriver(debuggingPort, chromeDriverPath):
    options = Options()
    options.add_experimental_option("debuggerAddress", f"localhost:{debuggingPort}")
    options.add_argument(f"webdriver.chrome.driver={chromeDriverPath}")
    options.add_argument("--disable-notifications")
    return webdriver.Chrome(options=options)

def cleanupChrome(driver, chromeApp):
    driver.quit()
    if chromeApp is not None:
        chromeApp.terminate()
        try:
            chromeApp.wait(timeout=5)
        except subprocess.TimeoutExpired:
            print("Force terminating Chrome...")
            chromeApp.kill()

        try:
            if os.name == 'nt':
                subprocess.run(['taskkill', '/F', '/IM', 'chrome.exe'], 
                             stdout=subprocess.DEVNULL, 
                             stderr=subprocess.DEVNULL)
            else:
                subprocess.run(['pkill', '-f', 'chrome'], 
                             stdout=subprocess.DEVNULL, 
                             stderr=subprocess.DEVNULL)
        except Exception as e:
            print(f"Error cleaning up Chrome processes: {e}")

if __name__ == "__main__":
    chromeDataDir = os.path.join(os.getcwd(), 'chromeData')
    if not os.path.exists(chromeDataDir):
        os.makedirs(chromeDataDir)
        print(f"'{chromeDataDir}' directory was created.")
    else:
        print(f"'{chromeDataDir}' directory already exists.")

    chromeApp = startChrome(debuggingPort, chromeUserDataDir, chromeAppPath)
    driver = setupChromeDriver(debuggingPort, chromeDriverPath)

    driver.get("https://www.linkedin.com/jobs/view/4077912250/?eBP=NON_CHARGEABLE_CHANNEL&refId=SFSD565YzVQ%2BZlWyb7iGbw%3D%3D&trackingId=Lq4e6FNPm60Lbh1%2FaEAF3A%3D%3D&trk=flagship3_search_srp_jobs")
    
    try:
        topCardDiv = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "jobs-apply-button--top-card"))
        )
        print("Found the top card div")
        
        easyApplyButton = topCardDiv.find_element(By.CLASS_NAME, "jobs-apply-button")
        easyApplyButton.click()
        print("Successfully clicked Easy Apply button")
        
        # Keep track of previous form HTML to detect when we're stuck on same page
        previous_form_html = ""
        same_page_count = 0
        max_same_page_attempts = 1  # Maximum number of times to try same page
        
        while True:
            time.sleep(1)
            form_modal = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, "jobs-easy-apply-modal"))
            )
            current_form_html = form_modal.get_attribute('outerHTML')
            
            # Check if we're stuck on the same page
            if current_form_html == previous_form_html:
                same_page_count += 1
                print(f"Warning: Same form detected ({same_page_count}/{max_same_page_attempts})")
                if same_page_count >= max_same_page_attempts:
                    print("Breaking loop - stuck on same page")
                    break
            else:
                same_page_count = 0
                
            # Send the HTML data to our scraping function
            print("\n=== Processing New Form Page ===")
            readTheInputsFrom(current_form_html)
            
            # Store current form HTML for next comparison
            previous_form_html = current_form_html
            
            # Sleep for 1 second
            
            try:
                # Find and click the Next button in the footer
                footer = driver.find_element(By.TAG_NAME, "footer")
                next_button = footer.find_element(By.CSS_SELECTOR, "button[aria-label='Continue to next step']")
                next_button.click()
                print("Successfully clicked Next button")
            except Exception as e:
                print("No more Next buttons found - likely reached end of application")
                break
                
    except TimeoutException:
        print("Error: Top card div or form modal not found within 5 seconds")
    except Exception as e:
        print(f"Error: An error occurred: {e}")
        
    input("Press Enter to close the browser...")
    cleanupChrome(driver, chromeApp)
