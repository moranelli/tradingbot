import json
import requests
from brokers.bybit_exchange import check_orders, check_position, get_balance, get_position, get_order, set_leverage, create_order, cerrar_posiciones, cancelar_ordenes, get_ticker_with_queue, check_position_with_queue, get_position_with_queue, get_order_with_queue, check_order_with_queue, obtener_kline_symbol
from datetime import datetime
import time
from time import strftime, gmtime
import math
import logging
from scripts.telegrambot import telegram_bot_sendtext
from scripts.indicators import get_atr, get_rsi, get_ema, get_sma, get_wma, get_hma2, get_hma3, get_hma2_prev_bar,get_hma3_prev_bar
from utils import log, errors
import threading
from config import bybit_config
from web import main

logger_bot_indicator = log.setup_custom_logger('botIndicator', filename='log/bybit_bit_indicator.log', console=True, log_level=logging.DEBUG)

class BotIndicator():

    def __init__(self, exchange=None, data=None, symbol=None, timeframe=None, info_symbol=None, ws=None, bot_indicator_event=None):
        self.exchange = exchange
        self.data = data
        self.symbol = symbol
        self.timeframe = timeframe
        self.info_symbol = info_symbol
        self.ws = ws
        self.bot_indicator_event = bot_indicator_event

    def botIndicator(self):
        logger_bot_indicator.info("Inicio de botIndicator...")

        info = []
        crossover_hull = 0
        crossunder_hull = 0
        # cross_hull_flag = 0
        # is_prev_bar_confirmed = False
        # current_bar_time = None
        confirmed_bar_time = None

        while(not self.bot_indicator_event.is_set()):
            current_time_utc = datetime.now().timestamp()

            candle = self.ws.ws_unauth.fetch('candle.' + str(self.timeframe) + '.' + str(self.symbol))
            while(not self.bot_indicator_event.is_set() and (candle['confirm'] == False or candle['start'] == confirmed_bar_time)):
                #print(candle)
                candle = self.ws.ws_unauth.fetch('candle.' + str(self.timeframe) + '.' + str(self.symbol))
                time.sleep(0)

            #while(not self.bot_indicator_event.is_set()):
                #print(self.ws.ws_unauth.fetch('candle.' + str(self.timeframe) + '.' + str(self.symbol)))
                #print("Vela NO confirmada")


            if(self.bot_indicator_event.is_set()):
                break

            if(candle['confirm'] == True):
                # is_prev_bar_confirmed = True
                confirmed_bar_time = candle['start']
                # current_bar_time = candle['end']
                print("Vela CONFIRMADA")

            kline_symbol = obtener_kline_symbol(exchange=self.exchange, symbol=self.symbol, timeframe=self.timeframe, time_from=current_time_utc, limit=200)
            for f in kline_symbol:
                info.append({ "open_time" : f['open_time'], "close" : f['close'], "low" : f['low'], "high" : f['high'] })

            #print(info)
            #print("rsi:  ", get_rsi(exchange=self.exchange, symbol=self.symbol, timeframe=self.timeframe, rsi_period=14, data=info))
            #print("ema:  ", get_ema(exchange=self.exchange, symbol=self.symbol, timeframe=self.timeframe, ma_period=None, data=info))
            ema20 = get_ema(exchange=self.exchange, symbol=self.symbol, timeframe=self.timeframe, ma_period=16, data=info)
            #print("sma:  ", get_sma(exchange=self.exchange, symbol=self.symbol, timeframe=self.timeframe, ma_period=None, data=info))
            sma50 = get_sma(exchange=self.exchange, symbol=self.symbol, timeframe=self.timeframe, ma_period=58, data=info)
            #print("wma:  ", get_wma(exchange=self.exchange, symbol=self.symbol, timeframe=self.timeframe, ma_period=None, data=info))
            hma2 = get_hma2(exchange=self.exchange, symbol=self.symbol, timeframe=self.timeframe, ma_period=11, data=info)
            hma2_prev_bar = get_hma2_prev_bar(exchange=self.exchange, symbol=self.symbol, timeframe=self.timeframe, ma_period=11, data=info)
            #print("hma2: ", hma2)
            hma3 = get_hma3(exchange=self.exchange, symbol=self.symbol, timeframe=self.timeframe, ma_period=11, data=info)
            hma3_prev_bar = get_hma3_prev_bar(exchange=self.exchange, symbol=self.symbol, timeframe=self.timeframe, ma_period=11, data=info)
            #print("hma3: ", hma3)
            # hma2_all = get_hma2_all(exchange=self.exchange, symbol=self.symbol, timeframe=self.timeframe, ma_period=None, data=info)

            # if(hma2 < hma3):
            #     crossunder_hull = 1
            #     if(crossover_hull == 1):
            #         crossover_hull = 0
            #         cross_hull_flag = 1
            #     else:
            #         cross_hull_flag = 0

            if(hma2 < hma3 and hma2_prev_bar >= hma3_prev_bar):
                crossover_hull = 0
                crossunder_hull = 1
            #     if(crossover_hull == 1):
            #         crossover_hull = 0
            #         cross_hull_flag = 1
            #     else:
            #         cross_hull_flag = 0

            # if(hma2 > hma3):
            #     crossover_hull = 1
            #     if(crossunder_hull == 1):
            #         crossunder_hull = 0
            #         cross_hull_flag = 1
            #     else:
            #         cross_hull_flag = 0
            if(hma2 > hma3 and hma2_prev_bar <= hma3_prev_bar):
                crossunder_hull = 0
                crossover_hull = 1
            #     if(crossunder_hull == 1):
            #         crossunder_hull = 0
            #         cross_hull_flag = 1
            #     else:
            #         cross_hull_flag = 0

            #print(int(info[-1]['open_time'])*1000)
            #if(crossunder_hull == 1 and cross_hull_flag == 1 and ema20 >= sma50):
            if(crossunder_hull == 1 and ema20 >= sma50):
            #if(1 == 1):
                print("---------------------------------------------------------------")
                print("open_time: " , datetime.fromtimestamp(int(info[-1]['open_time'])))
                print("LONG")
                print("hma2: ", hma2)
                print("hma3: ", hma3)
                print("hma2_prev_bar: ", hma2_prev_bar)
                print("hma3_prev_bar: ", hma3_prev_bar)
                open_time = int(str(int(info[-1]['open_time'])*1000))
                close = float(info[-1]['close'])
                order_action = "buy"
                position_side = "long"
                order_id = "hawk_buy_order"
                sl_atr = 0.8
                reward_ratio = 1.3
                print("---------------------------------------------------------------")
                data = {"passphrase": "yourpassphrasepoxy", "time": open_time, "exchange": "BYBIT", "ticker": self.symbol, "bar": { "bar_open_time": open_time, "close": close, "high_prev": 306.3, "low_prev": 305.7, "volume": 0 }, "strategy": { "order_action": order_action, "order_price": close, "order_id": order_id, "position_side": position_side, "sl_atr": sl_atr, "reward_ratio": reward_ratio}}
                print(data)
                main.start_strategy(data)

            if(crossover_hull and ema20 < sma50):
            #if(1==0):
                print("---------------------------------------------------------------")
                print("open_time: " , datetime.fromtimestamp(int(info[-1]['open_time'])))
                print("SHORT")
                print("hma2: ", hma2)
                print("hma3: ", hma3)
                open_time = int(str(int(info[-1]['open_time'])*1000))
                close = float(info[-1]['close'])
                order_action = "sell"
                position_side = "short"
                order_id = "hawk_sell_order"
                sl_atr = 0.8
                reward_ratio = 1.3
                print("---------------------------------------------------------------")
                data = {"passphrase": "yourpassphrasepoxy", "time": open_time, "exchange": "BYBIT", "ticker": self.symbol, "bar": { "bar_open_time": open_time, "close": close, "high_prev": 306.3, "low_prev": 305.7, "volume": 0 }, "strategy": { "order_action": order_action, "order_price": close, "order_id": order_id, "position_side": position_side, "sl_atr": sl_atr, "reward_ratio": reward_ratio}}
                main.start_strategy(data)

            # time.sleep(2)

        logger_bot_indicator.info("Fin de botIndicator...")
