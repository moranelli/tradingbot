import logging
import sys

FORMATTER = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

loggers = {}

def get_console_handler():
   console_handler = logging.StreamHandler(sys.stdout)
   console_handler.setFormatter(FORMATTER)
   return console_handler

def get_file_handler(filename):
   file_handler = logging.FileHandler(filename)
   file_handler.setFormatter(FORMATTER)
   return file_handler

def setup_custom_logger(name, filename=None, console=True, log_level=logging.DEBUG):
    if loggers.get(name):
        return loggers[name]

    logger = logging.getLogger(name)
    loggers[name] = logger

    logger.setLevel(log_level)

    if(not filename is None and console == True):
        logger.addHandler(get_console_handler())
        logger.addHandler(get_file_handler(filename))
    elif(not filename is None and console == False):
        logger.addHandler(get_file_handler(filename))
    else:
        logger.addHandler(get_console_handler())
    
    # with this pattern, it's rarely necessary to propagate the error up to parent
    logger.propagate = False

    return logger
