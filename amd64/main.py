
import os, math, sys, json, traceback, itertools
from datetime import datetime, timedelta
import concurrent.futures
from helper import get_driver, get_twilio, get_logger, check_resy

log_fname = os.path.join(os.getcwd(), 'log.txt')

logger = get_logger(log_fname)


def grouper(
	num_of_groups, 
	iterable, 
	fillvalue=None
):
	"grouper(3, 'ABCDEFG', 'x') --> ABC DEF Gxx"
	args = [iter(iterable)] * num_of_groups
	return list(itertools.zip_longest(fillvalue=fillvalue, *args))


def check_for_availability(
	restaurant_payload,
	driver, 
	twilio_client
):
	restaurant = restaurant_payload['restaurant']
	seats = restaurant_payload['seats']

	for delta in range(0, restaurant_payload['reservation_day_range']):

		ts = datetime.now() + timedelta(days=delta)

		url = f'https://resy.com/cities/ny/{restaurant}?date={ts.strftime("%Y-%m-%d")}&seats={seats}'

		button_list = check_resy(
			url,
			driver
		)
		
		if button_list:
			message = f'Availability at {restaurant}...\n\n{ts.strftime("%m-%d-%Y")}\n{url}'
			print(message)

			twilio_client.messages.create(
				body=message,
				from_=restaurant_payload['from'],
				to=restaurant_payload['to']
			)


def thread_task(
	restaurant_payloads
):
	if not restaurant_payloads:
		return
	
	driver = None

	try:
		driver = get_driver()
	except:
		print(traceback.format_exc())
		raise()

	twilio_client = None

	try:
		twilio_client = get_twilio(
			account_sid=os.environ['TWILIO_ACCOUNT_SID'],
			auth_token=os.environ['TWILIO_AUTH_TOKEN']
		) 
	except:
		print(traceback.format_exc())
		raise Exception('Unable to get twilio client')

	try:
		for restaurant_payload in restaurant_payloads:
			check_for_availability(restaurant_payload, driver, twilio_client)
	except:
		pass
	finally:
		driver.quit()
		

def ThreadPoolExecutor(payload, num_workers=4):
	
	try:
		group_size = math.ceil((len(payload)/num_workers))
		groups = grouper(group_size, payload, None)
		
		with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
			executor.map(thread_task, groups)
		
		return True
	except:
		print(traceback.format_exc())
		logger.info(traceback.format_exc())


if __name__ == "__main__":

	payload = None

	try:
		with open('payload.json', 'r') as f:
			payload = json.loads(f.read())['query']
		
		if payload is None:
			raise Exception('No payload')
	except:
		print(traceback.format_exc())
		raise Exception('Unable to get payload')

	try:
		ThreadPoolExecutor(payload)
	except:
		print(traceback.format_exc())
		raise Exception('Unable to complete ThreadPoolExecutor')
