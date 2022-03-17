import os
import time
from datetime import datetime, timedelta
from twilio.rest import Client

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

from webdriver_manager.chrome import ChromeDriverManager

from selenium.webdriver.chrome.service import Service

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

driver = webdriver.Chrome(
		options=chrome_options, 
		service=Service(ChromeDriverManager().install())
	)
 
account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']
client = Client(account_sid, auth_token)

seats = 2
restaurant = 'jackdaw'


if __name__ == "__main__":

	# check 30 days for availability
	for d in range(30, -1, -1):

		ts = datetime.now() + timedelta(days=d)

		url = f'https://resy.com/cities/ny/{restaurant}?date={ts.strftime("%Y-%m-%d")}&seats={seats}'

		driver.get(url)

		# https://selenium-python.readthedocs.io/locating-elements.html#
		button_list = driver.find_elements(By.CLASS_NAME, 'content-layer')

		availablity = '\n\t'.join([str(button.text).replace("\n", " - ") for button in button_list])

		if availablity:
			message = f'Availability at {restaurant}...\n\n{ts.strftime("%m-%d-%Y")}\n{url}'
			client.messages \
					.create(
						body=message,
						from_='+1(active twilio number to send notification from)',
						to=['+1(number to send notification to)']
					)

		time.sleep(1)