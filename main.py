
import os, sys, math, json, traceback
from datetime import datetime, timedelta
import concurrent.futures
import argparse

from selenium import webdriver
from twilio.rest import Client

from helper import grouper, get_browser, get_twilio, get_logger, check_resy, notify
from payload import payload

parser = argparse.ArgumentParser()
parser.add_argument('-m', '--mode', dest='mode', choices=['arch', 'amd64'], default='amd64')
parser.add_argument('-f', '--file', dest='file', default='query.json')

logger = get_logger(
	log_fname = os.path.join(os.getcwd(), 'log.txt')
)


def process_payload(
	payload: payload,
	browser: webdriver,
	twilio: Client
):
	'''
	Description:
		process payload by checking if theres any availability on resy.com
		by using an invocation of selenium.webdriver, twilio.rest.Client, and "check_resy"
		if availability exists, send an SMS message to interested parties

	Parameters:
		payload (payload): 				payload that should be processed
		browser (selenium.webdriver): 	invocation to be used to process web requests
		twilio 	(twilio.rest.Client): 	invocation to be used to process notifications
	'''

	availability = check_resy(
		url = payload.url,
		browser = browser,
		min_hour = payload.min_hour,
		max_hour = payload.max_hour
	)
	
	n_availability = len(availability)

	logger.info(f"[{n_availability} slots] {payload.url}")

	if availability:
		for number_to in payload.number_to:
			notify(
				restaurant = payload.restaurant,
				date = payload.date.strftime('%a, %m-%d-%Y'),
				availability = availability,
				seats = payload.seats,
				number_to = number_to,
				number_from = payload.number_from,
				url = payload.url,
				twilio = twilio
			)


def thread_task(
	payloads: list[payload]
):
	'''
	Description:
		process list of payloads using "process_payload" and
		an invocation of selenium.webdriver and twilio.rest.Client

	Parameters:
		payloads (list[payload]): list of payloads containing
			information that should be processed
	'''

	browser = None

	try:
		if not payloads:
			return

		args = parser.parse_args()	
		
		browser = get_browser(
			mode=args.mode
		)

		twilio = get_twilio(
			account_sid=os.environ['TWILIO_ACCOUNT_SID'],
			auth_token=os.environ['TWILIO_AUTH_TOKEN']
		) 

		for payload in payloads:
			process_payload(
				payload	= payload,
				browser	= browser,
				twilio	= twilio
			)
	
	except:
		print(traceback.format_exc())
		logger.info(traceback.format_exc())
	
	finally:
		if browser is not None:
			browser.quit()
		

def ThreadPoolExecutor(
	payloads: list[payload], 
	num_workers: int =2
):
	'''
	Description:
		Distribute payloads across "num_workers" number
		of threads to be processed concurrently using 
		"thread_task"

	Parameters:
		payloads 	(list[payload]): list of payloads containing
			information that should be processed concurrently
		num_workers (int): number of threads that should be spawned 
			to process payloads
	'''

	try:
		groups = grouper(
			num_of_groups = math.ceil((len(payloads)/num_workers)), 
			iterable = payloads
		)

		with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
			executor.map(thread_task, groups)
		
	except:
		print(traceback.format_exc())
		logger.info(traceback.format_exc())


if __name__ == "__main__":

	# CREATE DIRECTORY FOR LOGGING NOTIFICATIONS
	if not os.path.exists('notifications'):
		os.makedirs('notifications')

	query = None

	# READ QUERY FILE
	args = parser.parse_args()	

	try:
		with open(args.file, 'r') as f:
			query = json.loads(f.read())['query']
		
		if query is None:
			raise Exception('No query found')
	
	except Exception as e:
		logger.info(traceback.format_exc())
		sys.exit(1)

	payloads = []

	# GENERATE LIST OF PAYLOADS TO PROCESS
	try:
		for entry in query:

			dates = []

			if 'day_range' in entry.keys():
				for i in range(0, entry['day_range']):
					
					date = datetime.now() + timedelta(days=i)
 
					if date.weekday() >= entry['min_dow'] and date.weekday() <= entry['max_dow']:
						dates.append(date)

			elif 'date' in entry.keys():
				date = datetime.strptime(entry['date'], '%m-%d-%Y')

				dates.append(date)


			for date in dates:
				payloads.append(payload(
					restaurant = entry['restaurant'],
					state = entry['state'],
					seats = entry['seats'],		
					date = date,
					min_hour = entry['min_hour'],	
					max_hour = entry['max_hour'],	
					number_to = entry['number_to'],
					number_from = entry['number_from'],
				))

		if not payloads:
			raise Exception('No payloads')
		else:
			payloads = list(sorted(payloads, key=lambda d: d.date))

	except Exception as e:
		logger.info(traceback.format_exc())
		sys.exit(1)

	# PROCESS PAYLOADS USING IN THREADS
	try:
		ThreadPoolExecutor(payloads)

	except Exception as e:
		logger.info(traceback.format_exc())
		sys.exit(1)
