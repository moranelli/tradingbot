import csv
from datetime import datetime
from datetime import timedelta
from brokers.bybit_exchange import get_exchange, obtener_kline_symbol
import pandas as pd
import pandas_ta as ta
import json
import pytz

import os
import sys
sys.path.append("/home/poxy/Projects/tradingbot/app") 


def get_historical_data_to_csv(exchange=None, symbol=None, timeframe=None, time_from=None, limit=200):

    # datapath = ('data/2021_5minutes_sample_prod.csv')
    datapath = ('data/'+SYMBOL+'_2022_'+ str(timeframe) + 'minutes_prod.csv')

    candlesticks = obtener_kline_symbol(exchange=exchange, symbol=symbol, timeframe=timeframe, time_from=time_from, limit=limit)
    df = pd.DataFrame(columns=['id', 'symbol', 'period', 'interval', 'start_at', 'open_time', 'volume', 'open', 'high', 'low', 'close', 'turnover'])
    for candlestick in candlesticks:
        candlestick['open_time'] = datetime.fromtimestamp(candlestick['open_time'])
        df = df.append(candlestick, ignore_index=True)

    df.drop(columns=['id', 'symbol', 'period', 'interval', 'start_at', 'turnover'], inplace=True)
    df = df.rename(columns={"open_time": "datetime"})
    column_order_names = ["datetime", "high", "to_datetimelow", "open", "close", "volume"]
    df = df.reindex(columns=column_order_names)
    # Agrego columna con HL2 del precio
    df['hl2'] = ta.hl2(df['high'], df['low'])
    df.to_csv(datapath, encoding='utf-8', index=False)


def get_bybit_bars(exchange=None, symbol=None, timeframe=None, startTime=None, endTime=None):

    startTime = str(int(datetime.timestamp(startTime)))
    endTime   = str(int(datetime.timestamp(endTime)))

    # df = pd.DataFrame(json.loads(exchange.query_kline(symbol=symbol, interval=str(timeframe), **{'from':int(startTime), 'to':int(endTime)}))['result'])
    df = pd.DataFrame(exchange.query_kline(symbol=symbol, interval=str(timeframe), **{'from':int(startTime)})['result'])
    # df = pd.DataFrame(exchange.query_kline(symbol=symbol, interval=str(timeframe), **{'from':int(startTime), 'to':int(endTime)})['result'])

    if (len(df.index) == 0):
        return None

    df.index = [datetime.fromtimestamp(x) for x in df.open_time]

    return df


def get_historical_data_to_csv_v2(exchange=None, symbol=None, timeframe=None):

    df_list = []
    last_datetime = datetime(2022, 1, 1)
    while True:
        print(last_datetime)
        new_df = get_bybit_bars(exchange, symbol, timeframe, last_datetime, datetime.now())
        if new_df is None:
            break
        df_list.append(new_df)
        last_datetime = max(new_df.index) + timedelta(0, 1)

    df = pd.concat(df_list)
    df.drop(columns=['id', 'symbol', 'period', 'interval', 'start_at', 'turnover'], inplace=True)
    df['datetime'] = df['open_time'].apply(lambda x: datetime.fromtimestamp(x))
    df.drop(columns=['open_time'], inplace=True)
    column_order_names = ["datetime", "high", "low", "open", "close", "volume"]
    df = df.reindex(columns=column_order_names)
    df['hl2'] = ta.hl2(df['high'], df['low'])

    return df


if __name__ == "__main__":
    EXCHANGE_NAME = 'bybit'
    exchange = get_exchange()
    SYMBOL = "BTCUSDT"
    timeframe = 5
    current_time_utc = datetime.now().timestamp()

    # datapath = ('data/'+SYMBOL+'_2021_5minutes_prod.csv')
    datapath = ('data/'+SYMBOL+'_2022_'+ str(timeframe) + 'minutes_prod.csv')


    # get_historical_data_to_csv(exchange=exchange, symbol=SYMBOL, timeframe=timeframe, time_from=current_time_utc, limit=200)
    df = get_historical_data_to_csv_v2(exchange=exchange, symbol=SYMBOL, timeframe=timeframe)
    # print(df)
    df.to_csv(datapath, encoding='utf-8', index=False)