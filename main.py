
from glob import glob
import os, sys, math, json, traceback, itertools
from datetime import datetime, timedelta
import concurrent.futures
from helper import get_twilio, get_logger, check_resy, should_notify, amd64, arch
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-m', '--mode', dest='mode', choices=['arch', 'amd64'], default='amd64')

log_fname = os.path.join(os.getcwd(), 'log.txt')

if os.path.exists(log_fname):
	os.remove(log_fname)

logger = get_logger(log_fname)

os.environ['PYTHONHASHSEED'] = "0"

if not os.path.exists('notifications'):
	os.makedirs('notifications')


def zip_discard_compr(*iterables, sentinel=object()):
    return [[entry for entry in iterable if entry is not sentinel]
            for iterable in itertools.zip_longest(*iterables, fillvalue=sentinel)]

# https://stackoverflow.com/questions/38054593/zip-longest-without-fillvalue
def grouper(
	num_of_groups, 
	iterable, 
):
	"grouper(3, 'ABCDEFG', 'x') --> ABC DEF Gxx"
	args = [iter(iterable)] * num_of_groups
	
	return list(zip_discard_compr(*args))


def gen_payloads(
	query
):
	payloads = []

	for entry in query:

		restaurant = entry['restaurant']
		seats = entry['seats']

		if 'day_range' in entry.keys():

			for delta in range(0, entry['day_range']):

				ts = datetime.now() + timedelta(days=delta)

				if ts.weekday() < entry['min_dow'] or ts.weekday() > entry['max_dow']:
					continue
				
				url = f'https://resy.com/cities/ny/{restaurant}?date={ts.strftime("%Y-%m-%d")}&seats={seats}'

				payload = {'ts':ts, 'url':url, 'query':entry}

				payloads.append(payload) # memory leak, shouldnt need to store payload in urls array
		
		elif 'date' in entry.keys():

			ts = datetime.strptime(entry['date'], '%m-%d-%Y')

			url = f'https://resy.com/cities/ny/{restaurant}?date={ts.strftime("%Y-%m-%d")}&seats={seats}'

			payload = {'ts':ts, 'url':url, 'query':entry}

			payloads.append(payload) # memory leak, shouldnt need to store payload in urls array


	return list(sorted(payloads, key=lambda d: d['ts']))


def thread_task(
	payloads
):
	if not payloads:
		return

	driver = None

	try:
		args = parser.parse_args()	
		
		if args.mode == 'amd64':
			driver = amd64.get_driver()
		elif args.mode == 'arch':
			driver = arch.get_driver()

		driver.set_page_load_timeout(30)
				
		twilio_client = get_twilio(
			account_sid=os.environ['TWILIO_ACCOUNT_SID'],
			auth_token=os.environ['TWILIO_AUTH_TOKEN']
		) 

		for payload in payloads:

			availability = check_resy(
				url = payload['url'],
				driver = driver,
				min_hour = payload['query']['min_hour'],
				max_hour = payload['query']['max_hour']
			)
			
			button_num = len(availability)

			logger.info(f"[{button_num} btns] {payload['url']}")

			if availability:

				restaurant = payload['query']['restaurant']
				seats = payload['query']['seats']
				
				for number in payload['query']['to']:
					
					if should_notify(
						restaurant = restaurant,
						seats = seats,
						availability = availability,
						number = number
					):
						intro = 'reservation' if button_num == 1 else 'reservations'

						message = f"{button_num} {intro} available at {restaurant} for..." \
							f"\n\n{seats} people"\
							f"\n{payload['ts'].strftime('%a, %m-%d-%Y')}" \
							f"\n{payload['url']}"

						twilio_client.messages.create(
							body=message,
							from_= payload['query']['from'],
							to=number
						)

						break
			
	except:
		print(traceback.format_exc())
		logger.info(traceback.format_exc())
	
	finally:
		if driver is not None:
			driver.quit()
		

def ThreadPoolExecutor(payloads, num_workers=2):

	try:
		group_size = math.ceil((len(payloads)/num_workers))
		groups = grouper(group_size, payloads)

		with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
			executor.map(thread_task, groups)
		
	except:
		print(traceback.format_exc())
		logger.info(traceback.format_exc())


if __name__ == "__main__":

	query = None

	try:
		with open('query.json', 'r') as f:
			query = json.loads(f.read())['query']
		
		if query is None:
			raise Exception('No query found')
	
	except Exception as e:
		logger.info(traceback.format_exc())
		sys.exit(1)

	payloads = None

	try:
		payloads = gen_payloads(query)

		if payloads is None:
			raise Exception('No payloads')

	except Exception as e:
		logger.info(traceback.format_exc())
		raise e

	try:
		ThreadPoolExecutor(payloads)

	except Exception as e:
		logger.info(traceback.format_exc())
		raise e
