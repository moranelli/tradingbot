import sys
import json
import requests
from brokers.bybit_exchange import get_exchange, get_ticker, get_position, get_order
#from pybit import WebSocket
from websocket_poxy import WebSocket
from datetime import datetime
import time
from time import strftime,gmtime
import math

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
#from future.utils import iteritems

from config import bybit_config

import nest_asyncio
nest_asyncio.apply()

logger_ws = log.setup_custom_logger('websockets', filename='log/bybit_websockets.log', console=True, log_level=logging.DEBUG)

class BybitWebsocket():

    def __init__(self, symbol=None, info_symbol=None, q_ticker=None, q_order=None, q_position=None, timeframe=None):
        self.endpoint_public = bybit_config.WS_PUBLIC
        self.endpoint_private = bybit_config.WS_PRIVATE
        self.symbol = symbol
        self.info_symbol = info_symbol
        self.q_ticker = q_ticker
        self.q_order = q_order
        self.q_position = q_position
        self.timeframe = timeframe
        #self.ws_unauth = None
        #self.ws_auth = None
        # self.ws_load_queue = load_queue
        #self.__reset()


#     def __del__(self):
#         pass


    # def is_ws_connected(self):
    #     logger_ws.debug("Inicio funcion is_ws_connected...")

    #     response = False
    #     if(self.ws_auth is not None and self.ws_auth.exited is False):
    #         response = True

    #     logger_ws.debug("is_ws_connected: " + str(response))
    #     logger_ws.debug("Fin funcion is_ws_connected...")
    #     return response

    # def stop_websockets(self):
    #     logger_ws.info("Stopping websocket")
    #     if (self.ws_unauth is not None or self.ws_auth is not None):
    #         self.ws_auth.close()
    #         while self.ws_auth.sock:
    #             continue
    #         self.exited = True
    #         # self.ws_unauth.exit()
    #         # self.ws_auth.exit()
    #         #Forcebly set ws to None
    #         # self.ws_unauth = None
    #         # self.ws_auth = None
    #         logger_ws.info("Stopped websocket")
    #     else:
    #         logger_ws.info("websocket ya se encuentra finalizado")


    def connect(self):
        '''Connect to the websocket and initialize data stores.'''

        logger_ws.info("Starting connection to WebSocket.")

        subs_public = ['instrument_info.100ms.' + str(self.symbol), 'candle.' + str(self.timeframe) + '.' + str(self.symbol)]
        subs_private = ['order', 'position']


        logger_ws.info("Connecting to %s" % self.endpoint_public)
        # Connect without authentication!
        self.ws_unauth = WebSocket(
            endpoint=self.endpoint_public,
            subscriptions=subs_public,
            logging_level=logging.DEBUG,
            ping_interval=20,
            ping_timeout=10,
            restart_on_error=True,
            purge_on_fetch=True,
            max_data_length=20
        )
        logger_ws.info('Connected to WS. Waiting for data images, this may take a moment...')

        logger_ws.info("Connecting to %s" % self.endpoint_private)
        # Connect with authentication!
        self.ws_auth = WebSocket(
            endpoint=self.endpoint_private,
            subscriptions=subs_private,
            api_key=bybit_config.API_KEY,
            api_secret=bybit_config.API_SECRET,
            logging_level=logging.DEBUG,
            ping_interval=20,
            ping_timeout=10,
            restart_on_error=True,
            purge_on_fetch=True,
            max_data_length=20
        )
        logger_ws.info('Connected to WS. Waiting for data images, this may take a moment...')



#     #
#     # Lifecycle methods
#     #
#     def error(self, err):
#         logger_ws.debug("Inicio funcion error...")

#         self._error = err
#         logger_ws.error(err)
#         self.exit()
#         logger_ws.debug("Fin funcion error...")

#     def exit(self):
#         logger_ws.debug("Inicio funcion exit...")

#         self.ws.close()
#         while(self.is_ws_connected()):
#             time.sleep(1)
#         self.exited = True
#         logger_ws.debug("Fin funcion exit...")


#     #
#     # Private methods
#     #
#     def __connect(self, wsURL):
#         '''Connect to the websocket in a thread.'''
#         logger_ws.info("Starting thread")
#         self.ws = websocket.WebSocketApp(wsURL,
#                                          on_message=self.__on_message,
#                                          on_open=self.__on_open,
#                                          on_close=self.__on_close,
#                                          on_error=self.__on_error,
#                                          on_ping=self.__on_ping,
#                                          on_pong=self.__on_pong,
#                                          header=self.__get_auth()
#                                          )

#         self.wst = threading.Thread(name=self.subscription, target=lambda: self.ws.run_forever(ping_interval=5, ping_timeout=4))
#         self.wst.daemon = True
#         self.wst.start()

#         logger_ws.info("Started thread")

#         # Wait for connect before continuing
#         conn_timeout = 10
#         while (not self.ws.sock or not self.ws.sock.connected) and conn_timeout and not self._error:
#             time.sleep(1)
#             conn_timeout -= 1


#         if not conn_timeout or self._error:
#             logger_ws.debug("Connection timeout...")
#             logger_ws.error("Couldn't connect to WS! Exiting. Reintentando...")
#             # self.exit()
#             # sys.exit(1)

#         if(self.ws.sock.connected):
#             # Connected. Wait for subscriptions
#             if self.shouldAuth:
#                 self.ws.send(self.__get_auth())

#             logger_ws.info("Subscribing to %s" % self.subscription)
#             self.__send_command(self.send_command, self.subscription)
#             logger_ws.info("Subscribed to %s" % self.subscription)


#     def __on_ping(self, ws, message):
#         # logger_ws.debug(f'{str(datetime.now())}   ### Got a Ping! ###')
#         self.ws.send(json.dumps({"op": 'ping'}))
#         # logger_ws.info('### Got a Ping! ###' + str(self.ws.send(json.dumps({"op": 'ping'}))))


#     def __on_pong(self, ws, message):
#         # logger_ws.debug(f'{str(datetime.now())}   ### Send a Pong! ###')
#         self.ws.send(json.dumps({"op": 'ping'}))
#         # logger_ws.info('### Got a Pong! ###' + str(self.ws.send(json.dumps({"op": 'ping'}))))


#     def __get_auth(self):
#         '''Return auth headers. Will use API Keys if present in settings.'''

#         if self.shouldAuth is False:
#             return []

#         logger_ws.info("Authenticating with API Key.")
#         # To auth to the WS using an API key, we generate a signature of a nonce and
#         # the WS API endpoint.
#         expires = str(int(round(time.time())+5000))+"1000"
#         _val = 'GET/realtime' + str(expires)
#         signature = str(hmac.new(bytes(bybit_config.API_SECRET, "utf-8"), bytes(_val, "utf-8"), digestmod="sha256").hexdigest())

#         auth = {}
#         auth["op"] = "auth"
#         auth["args"] = [bybit_config.API_KEY, expires, signature]
#         args_secret = json.dumps(auth)

#         return args_secret


#     def __on_message(self, ws, message):
#         '''Handler for parsing WS messages.'''
#         message_req = message
#         message = json.loads(message)
#         # logger_ws.debug(json.dumps(message))

#         topic = message['topic'] if 'topic' in message else None
#         action = message['type'] if 'type' in message else message['action'] if 'action' in message else None
#         try:
#             if 'subscribe' in message_req:
#                 if message['success']:
#                     logger_ws.info("Subscribed to %s." % message['request']['args'])
#                 else:
#                     self.error("Unable to subscribe to %s. Error: \"%s\" Please check and restart." %
#                                (message['request']['args'][0], message['ret_msg']))
#             elif topic:
#                 if topic == "instrument_info.100ms." + str(self.symbol):
#                     self.__parse_ticker_message(action, message)
#                 elif topic == "position":
#                     self.__parse_position_message(action, message)
#                 elif topic == "order":
#                     self.__parse_order_message(action, message)
#                 else:
#                     raise Exception("Unknown topic: %s" % topic)
#         except:
#             logger_ws.error(traceback.format_exc())

#     def __send_command(self, command, args):
#         '''Send a raw command.'''
#         self.ws.send(json.dumps({"op": command, "args": args or []}))


#     def __on_open(self, ws):
#         logger_ws.info("Websocket Opened.")
#         logger_ws.debug("Inicializacion de queues")

#         if "instrument_info.100ms" in self.subscription[0]:
#             ticker = get_ticker(exchange=self.exchange, symbol=self.symbol)
#             if(ticker is None):
#                 ticker = {'symbol': self.symbol, 'last_price': self.LAST_PRICE, 'mark_price': self.MARK_PRICE, 'ask_price': self.ASK_PRICE, 'bid_price': self.BID_PRICE, 'last_tick_direction': self.LAST_TICK_DIRECTION}
#             else:
#                 ticker = {'symbol': self.symbol, 'last_price': float(ticker['last_price']), 'mark_price': float(ticker['mark_price']), 'ask_price': float(ticker['ask_price']), 'bid_price': float(ticker['bid_price']), 'last_tick_direction': ticker['last_tick_direction']}
#             self.ws_queue.put(ticker)

#         if "order" in self.subscription[0]:
#             limit_order = None
#             if(limit_order is None):
#                 order = {'symbol': self.symbol, 'order_id': self.ORDER_ID, 'order_link_id': self.ORDER_LINK_ID, 'side': self.SIDE, 'order_type': self.ORDER_TYPE, 'price': self.PRICE, 'qty': self.QTY, 'order_status': self.ORDER_STATUS}
#             else:
#                 order = {'symbol': self.symbol, 'order_id': self.ORDER_ID, 'order_link_id': self.ORDER_LINK_ID, 'side': self.SIDE, 'order_type': self.ORDER_TYPE, 'price': self.PRICE, 'qty': self.QTY, 'order_status': self.ORDER_STATUS}
#             self.ws_queue.put(order)

#         if "position" in self.subscription[0]:
#             open_pos_detail = get_position(exchange=self.exchange, symbol=self.symbol)
#             if(open_pos_detail is None):
#                 position = {'symbol': self.symbol, 'size': self.SIZE, 'entry_price': self.ENTRY_PRICE}
#             else:
#                 position = {'symbol': self.symbol, 'size': float(open_pos_detail['size']), 'entry_price': float(open_pos_detail['entry_price'])}
#             self.ws_queue.put(position)

#         logger_ws.debug("Fin de inicializacion de queues")

#     def __on_close(self, ws):
#         logger_ws.info('Websocket Closed')
#         # self.exit()
#         if not self.exited:
#             if (self.ws is not None):
#                 self.ws.on_message = None
#                 self.ws.on_open = None
#                 self.ws.on_close = None
#                 #self.exit()
#                 self.ws = None

#             logger_ws.info("Reconnecting to %s" % self.endpoint)
#             #Forcebly set ws to None
#             self.__connect(self.endpoint)
#             logger_ws.info('Reconnected to WS. Waiting for data images, this may take a moment...')


#     def __on_error(self, ws, error):
#         logger_ws.info('Websocket Error')
#         if not self.exited:
#             if (self.ws is not None):
#                 self.ws.on_message = None
#                 self.ws.on_open = None
#                 self.ws.on_close = None
#                 #self.exit()
#                 self.ws = None

#             logger_ws.info("Reconnecting to %s" % self.endpoint)
#             #Forcebly set ws to None
#             self.__connect(self.endpoint)
#             logger_ws.info('Reconnected to WS. Waiting for data images, this may take a moment...')



    #def __reset(self):
    #    self.exited = False
    #    self._error = None
        # self.LAST_PRICE = 0.0
        # self.MARK_PRICE = 0.0
        # self.ASK_PRICE = 0.0
        # self.BID_PRICE = 0.0
        # self.LAST_TICK_DIRECTION = ''
        # self.SYM = self.symbol
        # self.SIZE = 0.0
        # self.ENTRY_PRICE = 0.0
        # self.WALLET_BALANCE = 0.0
        # self.AVAILABLE_BALANCE = 0.0
        # self.ORDER_ID = ''
        # self.ORDER_LINK_ID = ''
        # self.SIDE = ''
        # self.ORDER_TYPE = ''
        # self.PRICE = 0.0
        # self.QTY = 0.0
        # self.ORDER_STATUS = ''


#     def __parse_ticker_message(self, action='', message=''):
#         if action == 'delta':
#             data = message['data']['update'][0]
#         elif action == 'snapshot':
#             data = message['data']
#         else:
#             data = None

#         if (data is not None):
#             if ('last_price_e4' in data):
#                 # self.LAST_PRICE =  int(data['last_price_e4']) * 0.0001
#                 self.LAST_PRICE = float("{:0.0{}f}".format(float(int(data['last_price_e4']) * 0.0001), self.info_symbol['pricePrecision']))
#             if ('mark_price_e4' in data):
#                 # self.MARK_PRICE =  int(data['mark_price_e4']) * 0.0001
#                 self.MARK_PRICE = float("{:0.0{}f}".format(float(int(data['mark_price_e4']) * 0.0001), self.info_symbol['pricePrecision']))
#             if ('ask1_price_e4' in data):
#                 # self.ASK_PRICE  =  int(data['ask1_price_e4']) * 0.0001
#                 self.ASK_PRICE  = float("{:0.0{}f}".format(float(int(data['ask1_price_e4']) * 0.0001), self.info_symbol['pricePrecision']))
#             if ('bid1_price_e4' in data):
#                 # self.BID_PRICE  =  int(data['bid1_price_e4']) * 0.0001
#                 self.BID_PRICE  = float("{:0.0{}f}".format(float(int(data['bid1_price_e4']) * 0.0001), self.info_symbol['pricePrecision']))
#             if ('last_tick_direction' in data):
#                 self.LAST_TICK_DIRECTION  = data['last_tick_direction']

#         ticker = {'symbol': self.symbol, 'last_price': self.LAST_PRICE, 'mark_price': self.MARK_PRICE, 'ask_price': self.ASK_PRICE, 'bid_price': self.BID_PRICE, 'last_tick_direction': self.LAST_TICK_DIRECTION}

#         # if(self.ws_load_queue.is_set()):
#         self.ws_queue.put(ticker)
#         # logger_ws.debug("Ticker: %s" % ticker)


#     def __parse_order_message(self, action='', message=''):
#         if action == '':
#             data = message['data'][0]
#         else:
#             data = None
#         if (data is not None):
#             if ('symbol' in data):
#                 self.SYM = data['symbol']
#             if ('order_id' in data):
#                 self.ORDER_ID = data['order_id']
#             if ('order_link_id' in data):
#                 self.ORDER_LINK_ID = data['order_link_id']
#             if ('side' in data):
#                 self.SIDE = data['side']
#             if ('order_type' in data):
#                 self.ORDER_TYPE = data['order_type']
#             if ('price' in data):
#                 self.PRICE = data['price']
#             if ('qty' in data):
#                 self.QTY = data['qty']
#             if ('order_status' in data):
#                 self.ORDER_STATUS = data['order_status']

#         order = {'symbol': self.SYM, 'order_id': self.ORDER_ID, 'order_link_id': self.ORDER_LINK_ID, 'side': self.SIDE, 'order_type': self.ORDER_TYPE, 'price': self.PRICE, 'qty': self.QTY, 'order_status': self.ORDER_STATUS}

#         # if(self.ws_load_queue.is_set()):
#         self.ws_queue.put(order)
#         # logger_ws.debug("Order: %s" % order)


#     def __parse_position_message(self, action='', message=''):
#         if action == 'update':
#             data = message['data'][0]
#         else:
#             data = None

#         if (data is not None):
#             if ('symbol' in data):
#                 self.SYM = data['symbol']
#             if ('size' in data):
#                 self.SIZE =  float(data['size'])
#             if ('entry_price' in data):
#                 # self.ENTRY_PRICE =  float(data['entry_price'])
#                 self.ENTRY_PRICE = float("{:0.0{}f}".format(float(data['entry_price']), self.info_symbol['pricePrecision']))

#         position = {'symbol': self.SYM, 'size': self.SIZE, 'entry_price': self.ENTRY_PRICE}

#         # if(self.ws_load_queue.is_set()):
#         self.ws_queue.put(position)
#         # logger_ws.debug("Position: %s" % position)


# # def toNearest(num, tickSize):
# #     """Given a number, round it to the nearest tick. Very useful for sussing float error
# #        out of numbers: e.g. toNearest(401.46, 0.01) -> 401.46, whereas processing is
# #        normally with floats would give you 401.46000000000004.
# #        Use this after adding/subtracting/multiplying numbers."""
# #     tickDec = Decimal(str(tickSize))
# #     return float((Decimal(round(num / tickSize, 0)) * tickDec))


if __name__ == "__main__":
    # create console handler and set level to debug

    SYMBOL = "BTCUSDT"

    q_ticker = queue.LifoQueue()
    q_position = queue.LifoQueue()
    q_order = queue.LifoQueue()
    stop_event = threading.Event()
    # start_load_queue_event = threading.Event()

    exchange = get_exchange()

    logger = log.setup_custom_logger('websocket', log_level=logging.DEBUG)
    ws = BybitWebsocket(symbol=SYMBOL, q_ticker=q_ticker, q_order=q_order, q_position=q_position)
    # ws_order = BybitWebsocket(exchange=exchange, symbol=SYMBOL, ws_queue=q_order, load_queue=start_load_queue_event)
    # ws_position = BybitWebsocket(exchange=exchange, symbol=SYMBOL, ws_queue=q_position, load_queue=start_load_queue_event)

    ws.connect()
    # ws_order.connect(endpoint=bybit_config.WS_PRIVATE, send_command="subscribe", subscription=["order"], shouldAuth=True)
    # ws_position.connect(endpoint=bybit_config.WS_PRIVATE, send_command="subscribe", subscription=["position"], shouldAuth=True)
    # cantidad = 0

    # if(ws.is_ws_connected()):
    #     print("Conectado")
    # else:
    #     print("NO Conectado")

    while True:
    #     # print(ws.ws_unauth.fetch('instrument_info.100ms.' + str(SYMBOL)))
    #     time.sleep(1.5)
    #     try:
    #         order = ws.ws_auth.fetch('order')
    #         if order:
    #             print(order)

    #         position = ws.ws_auth.fetch('position')
    #         if position:
    #             print(position)
    #     except Exception as e:
    #         print(e)
        time.sleep(2)
        order = ws.ws_auth.fetch('order')
        if order:
            # order = q_order.queue[q_order.qsize()-1]
            print("order: " + str(order))
            if order[0]['symbol'] == SYMBOL:
                limit_order = order

    # Start event Load Queues
    # start_load_queue_event.set()

    # while(True and not ws_ticker.exited and not ws_order.exited and not ws_position.exited):
    #     time.sleep(1)
    #     cantidad += 1
    #     if(cantidad == 5):
    #         ws_ticker.stop_websockets()
    #         ws_order.stop_websockets()
    #         ws_position.stop_websockets()
    #         #raise errors.CustomError(errors.ErrorCodes.ERR_SITUATION_2)
