import sys
from enum import Enum, unique, auto

class AuthenticationError(Exception):
    pass

class MarketClosedError(Exception):
    pass

class MarketEmptyError(Exception):
    pass

class OrderError(Exception):
    pass

class CustomError(Exception):
    """ Custom Exception """

    def __init__(self, error_code, message='', *args, **kwargs):

        # Raise a separate exception in case the error code passed isn't specified in the ErrorCodes enum
        if not isinstance(error_code, ErrorCodes):
            msg = 'Error code passed in the error_code param must be of type {0}'
            raise CustomError(ErrorCodes.ERR_INCORRECT_ERRCODE, msg, ErrorCodes.__class__.__name__)
        # Storing the error code on the exception object
        self.error_code = error_code
        # storing the traceback which provides useful information about where the exception occurred
        self.traceback = sys.exc_info()
        # Prefixing the error code to the exception message
        try:
            msg = '[{0}] {1}'.format(error_code.name, message.format(*args, **kwargs))
        except (IndexError, KeyError):
            msg = '[{0}] {1}'.format(error_code.name, message)
        super().__init__(msg)


# Error codes for all module exceptions
@unique
class ErrorCodes(Enum):
    ERR_INCORRECT_ERRCODE = auto()      # error code passed is not specified in enum ErrorCodes
    ERR_SITUATION_1 = auto()            # description of situation 1
    ERR_SITUATION_2 = 10001            # description of situation 2
    ERR_SITUATION_3 = auto()            # description of situation 3
    ERR_SITUATION_4 = auto()            # description of situation 4
    ERR_SITUATION_5 = auto()            # description of situation 5
    ERR_SITUATION_6 = auto()            # description of situation 6


def throw_exactly_matched_exception(self, exact, string, message):
    if string in exact:
        raise exact[string](message)