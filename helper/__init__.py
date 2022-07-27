import os, json, logging, traceback, hashlib, itertools
from datetime import datetime
from helper import amd64, arch
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
    value: str,
    max_length: int = 20
) -> str: 
    '''
	Description:
		Deterministic hashing function 

	Parameters:
		value       (str): string to be hashed
        max_length  (int): the max length of the hashed string

    Returns:
        hashed_string (str): hashed string
	'''

    return str(hashlib.md5(value.encode()).hexdigest()[:max_length])


# https://stackoverflow.com/questions/38054593/zip-longest-without-fillvalue
def zip_discard_compr(*iterables, sentinel=object()):
    return [[entry for entry in iterable if entry is not sentinel]
            for iterable in itertools.zip_longest(*iterables, fillvalue=sentinel)]


# https://stackoverflow.com/questions/38054593/zip-longest-without-fillvalue
def grouper(
	num_of_groups: int, 
	iterable, 
) -> list:
	'''
	Description:
		Group some iterable into "num_of_groups" number of groups.
		By default this function will provide no fill value for subgroups
		i.e. grouper(2, ['a','b','c']) -> [['a','b'], ['c']]

		this behavior was used because threads should not 
		need to process fill values

	Parameters:
		num_of_groups   (int): number of groups that iterable should be split into 
		browser         (selenium.webdriver): invocation to be used to process web requests
		twilio          (twilio.rest.Client): invocation to be used to process notifications

    Returns:
        (list): list of "num_of_groups" number of subgroups
	'''

	"grouper(3, 'ABCDEFG', 'x') --> ABC DEF Gxx"
	args = [iter(iterable)] * num_of_groups
	
	return list(zip_discard_compr(*args))


def get_logger(
    log_fname: str,
    truncate: bool = True
) -> logging.Logger:
    '''
	Description:
		provide an instance of logging.Logger that exports
        logs both to stdout and specified file. By default,
        the specified file will be truncated upon invoking
        this function.

    Parameters:
        log_fname (str): full path to file that where logs will be stored
        truncate  (bool): whether the log file should be truncated or not

    Returns:
        logger    (logging.Logger): 
    '''
    
    if truncate and os.path.exists(log_fname):
        os.remove(log_fname)

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

    logger = logging.getLogger('resy')

    logger.addHandler(fh)

    return logger


def get_browser(
    mode: str = 'amd',
    timeout: int = 30
) -> webdriver:
    '''
	Description:
		provide an instance of selenium.webdriver depending
        on host machine architecture. By default, host is assumed
        to have amd arch, however if you want to run this on
        something like a raspberry pi, please specify that the
        architecture is 'arch'

    Parameters:
        mode    (str): architecture of host machine
        timeout (int): number of seconds webdriver should wait before timeout

    Returns:
        browser (selenium.webdriver): instance that will be used to handle web requests
    '''

    if mode == 'amd64':
        browser = amd64.get_browser()
    elif mode == 'arch':
        browser = arch.get_browser()

    if timeout:
        browser.set_page_load_timeout(timeout)

    return browser


def get_twilio(
    account_sid: str,
    auth_token: str
) -> Client:
    '''
	Description:
		provide an instance of twilio.rest.Client

    Parameters:
        account_sid (str): provided twilio sid
        auth_token  (str): provided twilio auth token 

    Returns
        (Client): twilio client used to process notifications
    '''

    return Client(
        account_sid, 
        auth_token
    )


def check_resy(
    url: str, 
    browser: webdriver,
    min_hour: int = 18,
    max_hour: int = 22
) -> list[datetime]:		
    '''
    Description:
        check resy.com using instance of selenium.webdriver by searching for
        reservation buttons on webpage

    Parameters:
        url          (str): resy url to be checked
        browser      (selenium.webdriver): invocation to be used to process web requests
        min_hour	 (int): the earliest hour (24hr format) that would be acceptable
        max_hour	 (int): the latest hour (24hr format) that would be acceptable

    Returns
        availability (list[datetime]): available reservation times
    '''

    browser.get(url)

    # Wait until the page has been loaded
    # https://www.lambdatest.com/blog/selenium-wait-for-page-to-load/
    WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "VenuePage__Selector-Wrapper")))

    # Find reservation buttons
    # https://selenium-python.readthedocs.io/locating-elements.html#
    button_list = browser.find_elements(By.CLASS_NAME, 'ReservationButton__time')
    
    availability = []

    # availablity = '\n\t'.join([str(button.text).replace("\n", " - ") for button in button_list])
    for button in button_list:
        
        button_text = str(button.text).replace("\n", " - ")
        
        try:
            dt = datetime.strptime(button_text, '%I:%M%p')
        except:
            print(traceback.format_exc())
        
        if dt.hour >= min_hour and dt.hour < max_hour:
            availability.append(dt)

    return availability


def log_notifications(
    restaurant: str,
    date: str,
    availability: list[datetime],
    seats: int,
    number: str,
):
    '''
    Description:
        Populate 'notifications' directory with information about notifications
        that have been sent. This ensures that interested parties are not notified 
        too often.

    Parameters:
        restaurant 	 (str): name of restaurant as it appears in resy url
        date		 (datetime): when to search for availability
        availability (list[datetime]): available reservation times
        seats 		 (int): number of people attending
        number	     (str): phone number that should be notified
    '''

    now = datetime.now()

    for reservation_time in [r.strftime('%I:%M%p') for r in availability]:
        fname = hash_string(str((restaurant,date,reservation_time,seats,number)))
        fpath = os.path.join('notifications', fname)

        with open(fpath, 'w') as f: 
            f.write(
                json.dumps({
                'restaurant': restaurant,
                'date':date,
                'reservation_time': reservation_time,
                'seats': seats,
                'number': number,
                'notified': now.strftime('%Y-%m-%d %H:%M:%S')
                }, indent=2)
            )


def notify(
    restaurant: str,
    date: str, 
    availability: list[datetime],
    seats: int,
    number_to: str,
    number_from: str,
    url: str,
    twilio,
    threshold = 60,
):
    '''
    Description:
        populate 'notifications' directory with information about notifications
        that have been sent. This ensures that interested parties are not notified 
        too often.

    Parameters:
        restaurant 	 (str): name of restaurant as it appears in resy url
        date		 (str): when to search for availability
        availability (list[datetime]): available reservation times
        seats 		 (int): number of people attending
        number_to	 (str): phone number that should be notified
        number_from	 (str): twilio phone number that notification should be sent from
        threshold    (int): number of minutes that should pass before renotifying someone
    '''

    for reservation_time in [r.strftime('%I:%M%p') for r in availability]:

        fname = hash_string(str((restaurant,date,reservation_time,seats,number_to)))

        fpath = os.path.join('notifications', fname)

        should_notify = False

        if not os.path.exists(fpath):
            should_notify =  True
        else:
            with open(fpath, 'r') as f:
                contents = json.loads(f.read())
            
            notified = datetime.strptime(contents['notified'], '%Y-%m-%d %H:%M:%S')

            if (datetime.now() - notified).total_seconds() / 60.0 >= threshold:
                should_notify = True

        if should_notify:
            n_availability = len(availability)

            intro = 'reservation' if n_availability == 1 else 'reservations'

            message = f"{n_availability} {intro} available at {restaurant} for..." \
                f"\n\n{seats} people"\
                f"\n{date}" \
                f"\n{url}"

            twilio.messages.create(
                body = message,
                from_ = number_from,
                to = number_to
            )

            log_notifications(
                restaurant,
                date,
                availability,
                seats,
                number_to
            )

            return
