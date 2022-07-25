import os, json, logging, traceback, hashlib
from datetime import datetime
import traceback
from selenium import webdriver
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


# https://www.peterbe.com/plog/best-hashing-function-in-python
def hash_string(
    string
): 
    return hashlib.md5(string.encode()).hexdigest()[:20]


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
    driver,
    min_hour=18,
    max_hour=22
):		
    driver.get(url)

    # Wait until the page has been loaded
    # https://www.lambdatest.com/blog/selenium-wait-for-page-to-load/
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "VenuePage__Selector-Wrapper")))

    # Find reservation buttons
    # https://selenium-python.readthedocs.io/locating-elements.html#
    button_list = driver.find_elements(By.CLASS_NAME, 'ReservationButton__time')
    
    ret_list = []

    # availablity = '\n\t'.join([str(button.text).replace("\n", " - ") for button in button_list])
    for button in button_list:
        
        button_text = str(button.text).replace("\n", " - ")
        
        try:
            dt = datetime.strptime(button_text, '%I:%M%p')
        except:
            print(traceback.format_exc())
        
        if dt.hour >= min_hour and dt.hour <= max_hour:
            ret_list.append(dt)

    return ret_list


def populate(
    restaurant,
    seats,
    availability,
    number,
):
    now = datetime.now()

    for reservation_time in [r.strftime('%I:%M%p') for r in availability]:
        fname = hash_string(str((restaurant,seats,reservation_time,number)))
        fpath = os.path.join('notifications', fname)

        with open(fpath, 'w') as f: 
            f.write(
                json.dumps({
                'restaurant': restaurant,
                'seats': seats,
                'reservation_time': reservation_time,
                'number': number,
                'notified': now.strftime('%Y-%m-%d %H:%M:%S')
                }, indent=2)
            )


def should_notify(
    restaurant,
    seats,
    availability,
    number,
    threshold = 60
):
    for reservation_time in [r.strftime('%I:%M%p') for r in availability]:

        fname = hash_string(str((restaurant,seats,reservation_time,number)))

        fpath = os.path.join('notifications', fname)

        should_notify = False

        if not os.path.exists(fpath):
            should_notify =  True
        else:
            with open(fpath, 'r') as f:
                contents = json.loads(f.read())
            
            notified = datetime.strptime(contents['notified'], '%Y-%m-%d %H:%M:%S')

            if (datetime.now() - notified).total_seconds() /60.0 >= threshold:
                should_notify = True

        if should_notify:
            populate(
                restaurant,
                seats,
                availability,
                number
            )

        return should_notify

