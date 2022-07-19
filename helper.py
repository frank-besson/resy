import logging
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from twilio.rest import Client


# https://testdriven.io/blog/concurrent-web-scraping-with-selenium-grid-and-docker-swarm/

# options = webdriver.FirefoxOptions()
options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')


def get_logger(
    log_fname
):
    formatter = logging.Formatter(
        '%(asctime)s | %(name)s |  %(levelname)s: %(message)s'
    )

    fh = logging.FileHandler(log_fname)

    fh.setFormatter(formatter)

    logging.FileHandler(
        filename=log_fname,
        mode='w',
        delay=True
    )

    logging.basicConfig(
        format='%(levelname)s %(asctime)s %(message)s', 
        datefmt='%H:%M:%S',
        level=logging.INFO
    )

    logger = logging.getLogger('my_logger')

    logger.addHandler(fh)

    return logger


# https://testdriven.io/blog/concurrent-web-scraping-with-selenium-grid-and-docker-swarm/
def get_driver(
    options=options,
    host='http://localhost:4444/wd/hub'
):
    return webdriver.Remote(
        options=options, 
        # desired_capabilities=DesiredCapabilities.CHROME,
        command_executor = host
    )


def get_twilio(
    account_sid,
    auth_token
):
    return Client(
        account_sid, 
        auth_token
    )


def check_resy(
    url, 
    driver
):		
    driver.get(url)

    # Wait until the page has been loaded
    # https://www.lambdatest.com/blog/selenium-wait-for-page-to-load/
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "VenuePage")))

    # Find reservation buttons
    # https://selenium-python.readthedocs.io/locating-elements.html#
    return driver.find_elements(By.CLASS_NAME, 'ReservationButton__time')

    # availablity = '\n\t'.join([str(button.text).replace("\n", " - ") for button in button_list])
