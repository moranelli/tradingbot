"""Bot indicador
    """
from datetime import datetime
import time
import logging
import threading
import queue
#from scripts.telegrambot import telegram_bot_sendtext
from scripts.indicators import get_ema, SSLChannels, get_sma
from utils import log, errors
from config import bybit_config
from web import main
from brokers.bybit_exchange import obtener_kline_symbol, obtener_info_symbol, cambiar_margin_type_symbol, get_exchange, is_valid_passphrase, check_orders, check_position, get_info_symbol
from bybit_websocket import BybitWebsocket
import pandas as pd


logger_bot_indicator = log.setup_custom_logger('botIndicator', filename='log/bybit_bot_indicator.log', console=True, log_level=logging.DEBUG)

class BotIndicator():
    """Clase de Bot indicador
    """
    def __init__(self, exchange=None, data=None, symbol=None, timeframe=None, info_symbol=None, wst=None, bot_indicator_event=None):
        self.exchange = exchange
        self.data = data
        self.symbol = symbol
        self.timeframe = timeframe
        self.info_symbol = info_symbol
        self.wst = wst
        self.bot_indicator_event = bot_indicator_event

    def botIndicator(self):
        logger_bot_indicator.info("Inicio de botIndicator...")

        info = []
        #crossover_hull = 0
        #crossunder_hull = 0
        # cross_hull_flag = 0
        # is_prev_bar_confirmed = False
        # current_bar_time = None
        confirmed_bar_time = None
        buy_cond = False
        sell_cond = False


        while not self.bot_indicator_event.is_set():
            current_time_utc = datetime.now().timestamp()

            candle = self.wst.ws_unauth.fetch('candle.' + str(self.timeframe) + '.' + str(self.symbol))
            while(not self.bot_indicator_event.is_set() and (candle['confirm'] is False or candle['start'] == confirmed_bar_time)):
                #print(candle)
                candle = self.wst.ws_unauth.fetch('candle.' + str(self.timeframe) + '.' + str(self.symbol))
                time.sleep(0)

            #while(not self.bot_indicator_event.is_set()):
                #print(self.WST.WST_unauth.fetch('candle.' + str(self.timeframe) + '.' + str(self.symbol)))
                #print("Vela NO confirmada")

            #print(candle)
            if self.bot_indicator_event.is_set():
                break

            if candle['confirm'] is True:
                # is_prev_bar_confirmed = True
                confirmed_bar_time = candle['start']
                # current_bar_time = candle['end']
                #print("Vela CONFIRMADA")
                print("Vela CONFIRMADA")
                kline = []

            kline_symbol = obtener_kline_symbol(exchange=self.exchange, symbol=self.symbol, timeframe=self.timeframe, time_from=current_time_utc, limit=200)
            #print("kline_symbol: ", kline_symbol)
            for f in kline_symbol:
                kline.append({ "open_time" : f['open_time'], "open" : f['open'], "close" : f['close'], "low" : f['low'], "high" : f['high'] })
            #print("\n\kline: ", kline)

            #print("rsi:  ", get_rsi(exchange=self.exchange, symbol=self.symbol, timeframe=self.timeframe, rsi_period=14, data=info))
            #print("ema:  ", get_ema(exchange=self.exchange, symbol=self.symbol, timeframe=self.timeframe, ma_period=None, data=info))
            #ema20 = get_ema(exchange=self.exchange, symbol=self.symbol, timeframe=self.timeframe, ma_period=16, data=info)
            #print("sma:  ", get_sma(exchange=self.exchange, symbol=self.symbol, timeframe=self.timeframe, ma_period=None, data=info))
            info = get_ema(exchange=self.exchange, symbol=self.symbol, timeframe=self.timeframe, ma_period=10, data=kline)
            #ema10['open_time'] = pd.DatetimeIndex(pd.to_datetime(ema10['open_time'], unit='s')).tz_localize(tz='UTC').tz_convert('America/Argentina/Buenos_Aires')
            #print("ema10: ", ema10)
            info = get_ema(exchange=self.exchange, symbol=self.symbol, timeframe=self.timeframe, ma_period=55, data=info)
            #ema55['open_time'] = pd.DatetimeIndex(pd.to_datetime(ema55['open_time'], unit='s')).tz_localize(tz='UTC').tz_convert('America/Argentina/Buenos_Aires')
            #print("ema55: ", ema55)
            #sma50 = get_sma(exchange=self.exchange, symbol=self.symbol, timeframe=self.timeframe, ma_period=150, data=info)
            #ema50 = get_ema(exchange=self.exchange, symbol=self.symbol, timeframe=self.timeframe, ma_period=150, data=info)
            #print("wma:  ", get_wma(exchange=self.exchange, symbol=self.symbol, timeframe=self.timeframe, ma_period=None, data=info))
            #hma2 = get_hma2(exchange=self.exchange, symbol=self.symbol, timeframe=self.timeframe, ma_period=11, data=info)
            #hma2_prev_bar = get_hma2_prev_bar(exchange=self.exchange, symbol=self.symbol, timeframe=self.timeframe, ma_period=11, data=info)
            #print("hma2: ", hma2)
            #hma3 = get_hma3(exchange=self.exchange, symbol=self.symbol, timeframe=self.timeframe, ma_period=11, data=info)
            #hma3_prev_bar = get_hma3_prev_bar(exchange=self.exchange, symbol=self.symbol, timeframe=self.timeframe, ma_period=11, data=info)
            #print("hma3: ", hma3)
            # hma2_all = get_hma2_all(exchange=self.exchange, symbol=self.symbol, timeframe=self.timeframe, ma_period=None, data=info)
            #ssl = SSLChannel(info, period = self.p.ssl_period)
            #ssl = get_ssl(exchange=self.exchange, symbol=self.symbol, timeframe=self.timeframe, period=27, data=info)
            info = SSLChannels(exchange=self.exchange, symbol=self.symbol, timeframe=self.timeframe, period=9, data=info)
            #print("\nssl1: \n", ssl.to_string())

            #df['open_time'] = pd.to_datetime(df['open_time'], unit='s')
            #df['open_time'] = df_tmp['open_time'].apply(lambda x: datetime.fromtimestamp(x))
            #df = df.rename(columns={"open_time": "datetime"})
            #df['open_time'] = df['datetime'].apply(lambda timestamp: datetime.fromtimestamp(timestamp))
            #df['open_time'] = df['datetime'].apply(lambda x: datetime.fromtimestamp(x))
            #print(df)
            #df['date_time'] = [datetime.fromtimestamp(x) for x in df.open_time]

            info['open_time'] = pd.DatetimeIndex(pd.to_datetime(info['open_time'], unit='s')).tz_localize(tz='UTC').tz_convert('America/Argentina/Buenos_Aires')
            #df['open_time'].map(lambda x: pd.to_datetime(x, yearfirst=True).tz_convert('America/Argentina/Buenos_Aires'))
            #print(df['open_time'].dt.tz_localize(tz='America/Argentina/Buenos_Aires'))
            #df = df.tz_convert(tz = 'America/Argentina/Buenos_Aires')
            print("info: ", info)
            #ssl['open_time'] = ssl['open_time'].dt.tz_localize(tz='UTC').tz_convert('America/Argentina/Buenos_Aires')

            #print("ssl3: ", ssl.to_string())
            ## Set Conditions
            #buy_cond = bt.indicators.CrossUp(self.ssl.sslu, self.ssl.ssld, plot=False)
            #sell_cond = bt.indicators.CrossDown(self.ssl.sslu, self.ssl.ssld, plot=False)


            # if(hma2 < hma3):
            #     crossunder_hull = 1
            #     if(crossover_hull == 1):
            #         crossover_hull = 0
            #         cross_hull_flag = 1
            #     else:
            #         cross_hull_flag = 0

            #if(hma2 < hma3 and hma2_prev_bar >= hma3_prev_bar):
            print('Inicio validacion cruce')
            #open_time = info['open_time'].tail(1)
            #print(info['sslUp'])
            #print(info['sslUp'].iloc[-1])
            #print(info['sslUp'].iloc[-2])
            #print(info['sslDown'].iloc[-1])
            #print(info['sslDown'].iloc[-2])
            #print(info['ema' + str(10)].iloc[-1])
            #print(info['ema' + str(55)].iloc[-1])
            sell_cond = False
            buy_cond = False
            if(info['sslUp'].iloc[-1] > info['sslDown'].iloc[-1] and info['sslUp'].iloc[-2] <= info['sslDown'].iloc[-2]) and info['ema' + str(10)].iloc[-1] > info['ema' + str(55)].iloc[-1]:
                sell_cond = False
                buy_cond = True
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
            #if(hma2 > hma3 and hma2_prev_bar <= hma3_prev_bar):
            if(info['sslUp'].iloc[-1] < info['sslDown'].iloc[-1] and info['sslUp'].iloc[-2] >= info['sslDown'].iloc[-2]) and info['ema' + str(10)].iloc[-1] < info['ema' + str(55)].iloc[-1]:
                sell_cond = True
                buy_cond = False
            #     if(crossunder_hull == 1):
            #         crossunder_hull = 0
            #         cross_hull_flag = 1
            #     else:
            #         cross_hull_flag = 0

            #print(int(info[-1]['open_time'])*1000)
            #if(crossunder_hull == 1 and cross_hull_flag == 1 and ema20 >= sma50):
            #if(crossunder_hull == 1 and ema20 >= sma50):
            #open = float(info[-1]['open'])
            #print('Open info: ', open)
            #print(ssl['sslUp'].values[-1])
            #print('Open ssl: ', ssl['open'].values[-1])

            #if buy_cond and info[-1]['open'] > ema50 and :
            if buy_cond:
            #if(1 == 1):
                print("---------------------------------------------------------------")
                open_time = info['open_time'].iloc[-1]
                #print("open_time: " , datetime.fromtimestamp(int(info[-1]['open_time'])))
                print("open_time: " , open_time)
                print("LONG")
                #print("hma2: ", hma2)
                #print("hma3: ", hma3)
                #print("hma2_prev_bar: ", hma2_prev_bar)
                #print("hma3_prev_bar: ", hma3_prev_bar)
                #print(info['sslUp'].iloc[-1])
                #print(info['sslUp'].iloc[-2])
                #print(info['sslDown'].iloc[-1])
                #print(info['sslDown'].iloc[-2])
                #open_time = int(str(int(info[-1]['open_time'])*1000))
                open_price = float(info['open'].iloc[-1])
                close = float(info['close'].iloc[-1])
                order_action = "buy"
                position_side = "long"
                order_id = "hawk_buy_order"
                sl_atr = 0.8
                reward_ratio = 1.9
                print("---------------------------------------------------------------")
                data = {"passphrase": "yourpassphrasepoxy", "time": open_time, "exchange": "BYBIT", "ticker": self.symbol, "bar": { "bar_open_time": open_time, "open": open_price, "close": close, "high_prev": 306.3, "low_prev": 305.7, "volume": 0 }, "strategy": { "order_action": order_action, "order_price": close, "order_id": order_id, "position_side": position_side, "sl_atr": sl_atr, "reward_ratio": reward_ratio}}
                print(data)
                ##main.start_strategy(data)
                print("Fin señal bot indicator para long")

            #if(crossover_hull and ema20 < sma50):
            #if sell_cond and info[-1]['open'] < ema50:
            if sell_cond:
            #if(1==0):
                print("---------------------------------------------------------------")
                open_time = info['open_time'].iloc[-1]
                #print("open_time: " , datetime.fromtimestamp(int(info[-1]['open_time'])))
                print("open_time: " , open_time)
                print("SHORT")
                #print("hma2: ", hma2)
                #print("hma3: ", hma3)
                #print(info['sslUp'].iloc[-1])
                #print(info['sslUp'].iloc[-2])
                #print(info['sslDown'].iloc[-1])
                #print(info['sslDown'].iloc[-2])
                #open_time = int(str(int(info[-1]['open_time'])*1000))
                open_price = float(info['open'].iloc[-1])
                close = float(info['close'].iloc[-1])
                order_action = "sell"
                position_side = "short"
                order_id = "hawk_sell_order"
                sl_atr = 0.8
                reward_ratio = 1.9
                print("---------------------------------------------------------------")
                data = {"passphrase": "yourpassphrasepoxy", "time": open_time, "exchange": "BYBIT", "ticker": self.symbol, "bar": { "bar_open_time": open_time, "open": open_price, "close": close, "high_prev": 306.3, "low_prev": 305.7, "volume": 0 }, "strategy": { "order_action": order_action, "order_price": close, "order_id": order_id, "position_side": position_side, "sl_atr": sl_atr, "reward_ratio": reward_ratio}}
                print(data)
                ##main.start_strategy(data)
                print("Fin señal bot indicator para short")

            # time.sleep(2)
            #print(datetime.fromtimestamp(int(info[-1]['open_time'])), " - Sin alerta de indicadores")
            print(info['open_time'].iloc[-1], " - Sin alerta de indicadores")

        logger_bot_indicator.info("Fin de botIndicator...")


if __name__ == '__main__':
    EXCHANGE_NAME = 'bybit'
    SYMBOL = "BTCUSDT"
    TIMEFRAME = 5
    INFO_SYMBOL = ""

    WST = None
    q_ticker = queue.LifoQueue()
    q_position = queue.LifoQueue()
    q_order = queue.LifoQueue()

    botIndicator = None
    bot_indicator_event = threading.Event()

    EXCHANGE = None


    ## Validacion de Websockets
    #while WST is None:
    WST = main.start_websockets()

    ## Validacion de Exchange
    while EXCHANGE is None:
        EXCHANGE = get_exchange()

    if INFO_SYMBOL == "":
        INFO_SYMBOL = get_info_symbol(exchange=EXCHANGE, symbol=SYMBOL, info_symbol=INFO_SYMBOL)

    q_ticker.queue.clear()
    q_order.queue.clear()
    q_position.queue.clear()
    WST = BybitWebsocket(symbol=SYMBOL, q_ticker=q_ticker, q_order=q_order, q_position=q_position, timeframe=TIMEFRAME)
    WST.connect()

    print('*** Inicio de botIndicator ***')

    botIndicator = BotIndicator(exchange=EXCHANGE, data=None, symbol=SYMBOL, timeframe=TIMEFRAME, info_symbol=INFO_SYMBOL, wst=WST, bot_indicator_event=bot_indicator_event)
    botIndicator.botIndicator()
