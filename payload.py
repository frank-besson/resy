from datetime import datetime

class TypeException(Exception):
    """ custom exception class for type errors """


def check_type(obj, required_type):
    if type(obj) != required_type:
        raise TypeException('Incorrect type provided')
    else:
        return obj


class payload:

    def __init__(
        self, 
        restaurant: str,
        state: str,
        seats: int,		
        date: datetime,
        min_hour: int,	
        max_hour: int,	
        number_to: list,
        number_from: str,
    ):
        '''
        Parameters:
            restaurant 	(str): name of restaurant as it appears in resy url
            state       (str): state of restaurant as it appears in resy url
            seats 		(int): number of people attending
            date		(datetime): when to search for availability
            min_hour	(int): the earliest hour (24hr format) that would be acceptable
            max_hour	(int): the latest hour (24hr format) that would be acceptable
            number_to	(list[str]): list of phone numbers that should be notified
            number_from	(str): twilio number that notifications should be sent from
        '''

        self.restaurant  = check_type(restaurant, str)
        self.state       = check_type(state, str)
        self.seats	     = check_type(seats, int)
        self.date        = check_type(date, datetime)
        self.min_hour    = check_type(min_hour, int)
        self.max_hour    = check_type(max_hour, int)
        self.number_to   = check_type(number_to, list)
        self.number_from = check_type(number_from, str)

        self.url =  f'https://resy.com/cities/{state}/{restaurant}?date={date.strftime("%Y-%m-%d")}&seats={seats}'

