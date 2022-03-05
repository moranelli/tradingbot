## Imports
from json import loads, dumps
from brokers.bybit_exchange import cambiar_margin_type_symbol, get_exchange, is_valid_passphrase, check_orders, check_position, get_ticker, get_order, check_orders, get_balance, obtener_info_symbol, set_leverage, get_position, obtener_kline_symbol, get_info_symbol
from datetime import datetime
import time
from time import strftime, gmtime
import math
from scripts.telegrambot import telegram_bot_sendtext
from scripts.indicators import get_atr, get_ssl
from web import main
from fastapi import Request
from backtests.bot_indicator import BotIndicator

import os
import sys
sys.path.append("/home/poxy/Projects/tradingbot/app") 

# import talib
# import numpy as np
# import pandas as pd
# import pandas_ta as ta

#import cProfile
# import cProfile, pstats, io
# from pstats import SortKey
#from pyinstrument import Profiler
#from requests.models import Request
#import asyncio

# pr = cProfile.Profile()
# pr.enable()

#Inicio de Profiler
#profiler = Profiler()
#profiler.start()

# def truncate(n, decimals=0):
#     multiplier = 10 ** decimals
#     return int(n * multiplier) / multiplier

#class StrategyTest():
def strategy_test():
    # async def strategy_test(self):
    exchange = get_exchange()

    symbol = "BTCUSDT"

    # SL_ATR = 0.3
    # reward_ratio = 1.4
    # risk_perc = 5.0
    # entry_price = 16.2358
    # atr = 0.1081928571

    # SL_ret = entry_price - (atr * SL_ATR)
    # StopLoss = min(SL_ret, entry_price - (atr * 0.2))  #Cambio open_price por entry_price
    # StopLoss = float("{:0.0{}f}".format(float(StopLoss), 4))
    # TakeProfit = (entry_price + ((entry_price - StopLoss) * reward_ratio))
    # TakeProfit = float("{:0.0{}f}".format(float(TakeProfit), 4))
    # print("SL_ret: " + str(SL_ret))
    # print("StopLoss: " + str(StopLoss))
    # print("TakeProfit: " + str(TakeProfit))


    #print(strftime("%Y-%m-%d_%H:%M:%S", gmtime()))
    #print("archivo" + "_" +  strftime("%Y-%m-%d_%H-%M-%S", gmtime()))

    # server_time = client.Common.Common_getTime().result()[0]['time_now']
    # print("Bybit_time: " + str(server_time))
    # timestamp = datetime.now()
    # print("Local_time: " + str(timestamp))

    # timestamp_linux = time.time()
    # print("Local_time_Linux: " + str(timestamp_linux))

    # print(get_ticker(exchange, symbol))
    # print(check_position(exchange, symbol))
    # print(check_orders(exchange, symbol))
    # balance = get_balance(exchange=exchange, coin='USDT')

    # print(balance)
    # if(balance > 100):
    #     balance_details_size = 100.00
    # else:
    #     balance_details_size = balance
    # print(balance_details_size)
    #print(cambiar_tp_sl_mode(exchange, symbol))
    # print(obtener_info_symbol(exchange, symbol))
    # print(set_leverage(exchange, symbol, leverage=3))
    # order_tp_response = exchange.place_active_order(side='Buy', symbol=symbol, order_type='Limit', qty=76.9, price=19.715, order_link_id='hawk_order-2021-05-25_14-22-43', time_in_force='PostOnly', reduce_only=False, close_on_trigger=False)
    # print(order_tp_response)

    # print("POSSSS: ", get_position(exchange=exchange, symbol=symbol))


    ## ATR
    # now = datetime.datetime.utcnow()
    # since = now - datetime.timedelta(hours=1)
    # unixtime = calendar.timegm(since.utctimetuple())

    # resultado = exchange.query_kline(symbol=symbol, interval="3", **{'from':unixtime})['result']

    # df = pd.DataFrame(resultado[:-1])
    # df.drop(columns=['id', 'symbol', 'volume', 'open', 'period', 'interval', 'start_at','turnover'], inplace=True)
    # df['open_time'] = pd.to_datetime(df['open_time'], unit='s')

    # df['atr'] = ta.atr(df['high'], df['low'], df['close'], length=14, mamode="rma" )

    # print(df[-1:]['atr'].values[0])

    #print(get_atr(exchange=exchange, symbol=symbol, interval=3, periods=14))
    # current_time_utc = datetime.datetime.now().timestamp()
    # print(obtener_kline_symbol(exchange=exchange, symbol=symbol, timeframe=15, time_from=current_time_utc, limit=2)[0])
    # print(datetime.fromtimestamp(round(int("1626783000"))))

        #data = '{"passphrase": "yourpassphrasepoxy", "time": "1626474606293", "exchange": "BYBIT", "ticker": "BNBUSDT", "bar": {"bar_open_time": 1626474600000, "close": 305.35, "high_prev": 306.4, "low_prev": 305.15, "volume": 0}, "strategy": {"order_action": "sell", "order_price": 305.7928768148, "order_id": "hawk_sell_order", "position_side": "short", "sl_atr": 0.8, "reward_ratio": 1.3}}'
        # dumb_request = Request(
        #     {
        #         "type": "http",
        #         "method": "POST",
        #         "path": "/webhook",
        #         "query_string": data,
        #         "headers": {'content-type': 'application/json', 'user-agent': 'PostmanRuntime/7.28.2', 'accept': '*/*', 'cache-control': 'no-cache', 'postman-token': '6c55c062-9280-411f-b19a-8ab763fbeb9e', 'host': 'portalpox.duckdns.orgportalpox.duckdns.org:80', 'accept-encoding': 'gzip, deflate, br', 'connection': 'keep-alive', 'content-length': '44'},
        #     }
        # )

        # print(dumb_request)
        # json_object = json.load(str(data))
        # json_object = loads(data)
        # json_object = loads(data)
        # print(json_object)
    # print(int(datetime.now().timestamp()*1000))
    # print("1626611700000")
    # data = {"passphrase": "yourpassphrasepoxy", "time": "1626611710278", "exchange": "BYBIT", "ticker": "BNBUSDT", "bar": { "bar_open_time": 1626611700000, "close": 306.3, "high_prev": 306.3, "low_prev": 305.7, "volume": 0 }, "strategy": { "order_action": "buy", "order_price": 306.0503335694, "order_id": "hawk_buy_order", "position_side": "long", "sl_atr": 0.8, "reward_ratio": 1.3}}
    #main.start_strategy(data)
    # print(data)



    ## ATR




    # info_symbol = obtener_info_symbol(client, symbol)
    # print(info_symbol)

    # get_diff_time()
    # balance = get_balance(exchange)
    # print(balance)
    # server_time = exchange.Common.Common_get().result()
    # local_time = str(int(round(time.time())-1))+"000"

    # print("server_time:", server_time)
    # print("local_time:", local_time)

    # diff = 0
    # print("diff:", diff)

# def atr(data):
#     print(data)
#     data['previous_close'] = data['close'].shift(1)
#     data['high-low'] = abs(data['high'] - data['low'])
#     data['high-pc'] = abs(data['high'] - data['previous_close'])
#     data['low-pc'] = abs(data['low'] - data['previous_close'])

    # data['tr'] = data[['high-low', 'high-pc', 'low-pc']].max(axis=1)
    # data['tr'] = tr(data)
    # atr = data['tr'].rolling(period).mean()
    # data['atr'] = data['tr'].rolling(14).mean()
    # return atr

# def atr(data, period):
#     data['tr'] = tr(data)
    # atr = data['tr'].rolling(period).mean()

    # return atr

    exchange = get_exchange()
    SYMBOL = "BTCUSDT"
    timeframe = 5
    info_symbol = ""

    if(info_symbol == ""):
        info_symbol = get_info_symbol(exchange=exchange, symbol=SYMBOL, info_symbol=info_symbol)

    print(info_symbol)
    #botIndicator = BotIndicator(exchange=exchange, data=None, symbol=SYMBOL, timeframe=timeframe, info_symbol=info_symbol, ws=None, bot_indicator_event=None)
    #botIndicator

if __name__ == "__main__":
    strategy_test()
#    strategyTest = StrategyTest()
#    asyncio.run(strategyTest.strategy_test())



# pr.disable()
# s = io.StringIO()
# sortby = SortKey.CUMULATIVE
# ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
# ps.print_stats()
# print(s.getvalue())


#Fin de Profiler
#profiler.stop()
#print(profiler.output_text(unicode=True, color=True, show_all=True))
#print(profiler.output_text(unicode=True, color=True))

#cProfile.run('strategy_test()')
