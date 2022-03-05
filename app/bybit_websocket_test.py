import sys
import json
import requests
from brokers.bybit_exchange import get_exchange, get_ticker, get_position, get_order
#from pybit import WebSocket
from datetime import datetime
import time
from time import strftime,gmtime
import math

import websocket

import decimal
from decimal import Decimal

import asyncio
# import websocket
import json
import time
import hmac

import signal
import os
import functools
import threading, queue
import logging
from utils import log, errors
import traceback
from future.utils import iteritems

from config import bybit_config

import nest_asyncio
nest_asyncio.apply()

#logger_ws = log.setup_custom_logger('websockets', filename='log/bybit_websockets.log', console=True, log_level=logging.DEBUG)
logging.basicConfig(filename='log/logfile_wrapper.log', level=logging.ERROR, format='%(asctime)s %(levelname)s %(message)s')


#self.endpoint_public = bybit_config.WS_PUBLIC
#self.endpoint_private = bybit_config.WS_PRIVATE
#self.symbol = symbol
#self.info_symbol = info_symbol
#self.q_ticker = q_ticker
#self.q_order = q_order
#self.q_position = q_position
#self.timeframe = timeframe
#subs_public = ['instrument_info.100ms.' + str(self.symbol), 'candle.' + str(self.timeframe) + '.' + str(self.symbol)]
#subs_private = ['order', 'position']


    #def connect(self):
    #    '''Connect to the websocket and initialize data stores.'''
#
    #    logger_ws.info("Starting connection to WebSocket.")
#
    #    subs_public = ['instrument_info.100ms.' + str(self.symbol), 'candle.' + str(self.timeframe) + '.' + str(self.symbol)]
    #    subs_private = ['order', 'position']
#
#
    #    logger_ws.info("Connecting to %s" % self.endpoint_public)
    #    # Connect without authentication!
    #    self.ws_unauth = WebSocket(
    #        endpoint=self.endpoint_public,
    #        subscriptions=subs_public,
    #        logging_level=logging.DEBUG,
    #        ping_interval=20,
    #        ping_timeout=10,
    #        restart_on_error=True,
    #        purge_on_fetch=True,
    #        max_data_length=20
    #    )
    #    logger_ws.info('Connected to WS. Waiting for data images, this may take a moment...')
#
    #    logger_ws.info("Connecting to %s" % self.endpoint_private)
    #    # Connect with authentication!
    #    self.ws_auth = WebSocket(
    #        endpoint=self.endpoint_private,
    #        subscriptions=subs_private,
    #        api_key=bybit_config.API_KEY,
    #        api_secret=bybit_config.API_SECRET,
    #        logging_level=logging.DEBUG,
    #        ping_interval=20,
    #        ping_timeout=10,
    #        restart_on_error=True,
    #        purge_on_fetch=True,
    #        max_data_length=20
    #    )
    #    logger_ws.info('Connected to WS. Waiting for data images, this may take a moment...')


prev_send_time = int(time.time() * 1000)
topic = "orderBookL2_25.BTCUSDT"
trade_results = {}
size = {}
size_usdt = {}

def on_message(ws, message):
    data = json.loads(message)
    #print(data)

def on_error(ws, error):
    print('we got error')
    logging.error('we got error')
    print(error)
    print('print error complete')
    logging.error('print error complete')

def on_close(ws):
    print("### about to close please don't close ###")
    logging.error("### about to close please don't close ###")

def on_open(ws):
    print('opened')
    logging.error('opened')
    ws.send(json.dumps({"op": "subscribe", "args": [topic]}))

def on_pong(ws, *data):
    print('pong received')
    logging.error('pong received')

def on_ping(ws, *data):
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    print("date and time =", dt_string)
    logging.error("date and time =", dt_string)
    print('ping received')
    logging.error('ping received')

def connWS():
    ws = websocket.WebSocketApp(
        #"wss://stream.bybit.com/realtime",
        "wss://stream-testnet.bybit.com/realtime_public",
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
        on_ping=on_ping,
        on_pong=on_pong,
        on_open=on_open
    )
    ws.run_forever(
		#http_proxy_host='127.0.0.1',
		#http_proxy_port=1087,
		ping_interval=30,
		ping_timeout=10
	)


if __name__ == "__main__":
    # create console handler and set level to debug
    websocket.enableTrace(True)


    SYMBOL = "BTCUSDT"
    q_ticker = queue.LifoQueue()
    q_position = queue.LifoQueue()
    q_order = queue.LifoQueue()
    stop_event = threading.Event()
    exchange = get_exchange()
    #logger = log.setup_custom_logger('websocket', log_level=logging.DEBUG)
    #ws = BybitWebsocket(symbol=SYMBOL, q_ticker=q_ticker, q_order=q_order, q_position=q_position)
    connWS()

    #ws = BybitWebsocket(symbol=SYMBOL, q_ticker=q_ticker, q_order=q_order, q_position=q_position)
    #ws.connect()
    #
    #while True:
    #    time.sleep(2)
    #    order = ws.ws_auth.fetch('order')
    #    if order:
    #        print("order: " + str(order))
    #        if order[0]['symbol'] == SYMBOL:
    #            limit_order = order
