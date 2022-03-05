## Imports
import datetime
import calendar
import pandas as pd
import pandas_ta as ta
import math
#from backtrader.indicators import EMA, SMA, WMA
import backtrader as bt
import numpy as np

def get_atr(exchange=None, symbol=None, timeframe=None, periods=None):
    now = datetime.datetime.utcnow()
    since = now - datetime.timedelta(minutes=timeframe*periods*2)
    unixtime = calendar.timegm(since.utctimetuple())

    resultado = exchange.query_kline(symbol=symbol, interval=timeframe, **{'from':unixtime})['result']

    df = pd.DataFrame(resultado[:-1])
    df.drop(columns=['id', 'symbol', 'volume', 'open', 'period', 'interval', 'start_at','turnover'], inplace=True)
    df['open_time'] = pd.to_datetime(df['open_time'], unit='s')

    df['atr'] = ta.atr(df['high'], df['low'], df['close'], length=periods, mamode="rma" )

    # print(df[-1:]['atr'].values[0])
    return float(df[-1:]['atr'].values[0])


def get_rsi(exchange=None, symbol=None, timeframe=None, rsi_period=14, data=None):

    #RSI_OVERBOUGHT = 70
    #RSI_OVERSOLD = 30

    df = pd.DataFrame(data[:-1])
    df.drop(columns=['low', 'high'], inplace=True)
    df['open_time'] = pd.to_datetime(df['open_time'], unit='s')

    #print( df.ta.rsi(length=rsi_period, mamode="rma" )[-1] )
    df['rsi'] = df.ta.rsi(length=rsi_period, mamode="rma" )

    return float(df[-1:]['rsi'].values[0])


def get_ema(exchange=None, symbol=None, timeframe=None, ma_period=None, data=None):

    #df = pd.DataFrame(data[:-1])
    df = pd.DataFrame(data)
    #df.drop(columns=['low', 'high'], inplace=True)
    #df['open_time'] = pd.to_datetime(df['open_time'], unit='s')

    #print( ta.ema(df['close'], length=ema_period, mamode="rma" ) )
    # print( ta.ema(df['close'], length=ma_period )[-1] )
    #df['ema'] = ta.ema(df['close'], length=ma_period )
    df['ema' + str(ma_period)] = ta.ema(df['close'], length=ma_period )

    #return float(df[-1:]['ema'].values[0])
    return df

def get_sma(exchange=None, symbol=None, timeframe=None, ma_period=None, data=None):

    #df = pd.DataFrame(data[:-1])
    df = pd.DataFrame(data)
    #df.drop(columns=['low', 'high'], inplace=True)
    #df['open_time'] = pd.to_datetime(df['open_time'], unit='s')

    #print( ta.ema(df['close'], length=ema_period, mamode="rma" ) )
    # print( ta.sma(df['close'], length=ma_period )[-1] )
    df['sma' + str(ma_period)] = ta.sma(df['close'], length=ma_period )

    #return float(df[-1:]['sma'].values[0])
    return df

def get_sma_high(exchange=None, symbol=None, timeframe=None, period=None, data=None):

    #print('Inicio funcion get_hma_high')
    #df = pd.DataFrame(data[:-1])
    df = pd.DataFrame(data)
    #df = data
    #df['open_time'] = pd.to_datetime(df['open_time'], unit='s')
    #print(df)
    #p = period / 2
    df['sma_high'] = ta.sma(df['high'], length=period )
    #print(df['hma_high'])
    #return float(df[-1:]['hma_high'].values[0])
    return df['sma_high']
    #return float(df[-1:]['hma_high'].values[0])


def get_sma_low(exchange=None, symbol=None, timeframe=None, period=None, data=None):

    #print('Inicio funcion get_hma_high')
    #df = pd.DataFrame(data[:-1])
    df = pd.DataFrame(data)
    #df = data
    #df['open_time'] = pd.to_datetime(df['open_time'], unit='s')
    #print(df)
    #p = period / 2
    df['sma_low'] = ta.sma(df['low'], length=period )
    #print(df['hma_high'])
    #return float(df[-1:]['hma_high'].values[0])
    return df['sma_low']
    #return float(df[-1:]['hma_high'].values[0])


def get_wma(exchange=None, symbol=None, timeframe=None, ma_period=None, data=None):

    df = pd.DataFrame(data[:-1])
    df.drop(columns=['low', 'high'], inplace=True)
    df['open_time'] = pd.to_datetime(df['open_time'], unit='s')

    #print( ta.ema(df['close'], length=ema_period, mamode="rma" ) )
    # print( ta.wma(df['close'], length=ma_period )[-1] )
    df['wma'] = ta.wma(df['close'], length=ma_period )

    return float(df[-1:]['wma'].values[0])

def get_hma2(exchange=None, symbol=None, timeframe=None, ma_period=None, data=None):

    df = pd.DataFrame(data[:-1])
    #df.drop(columns=['low', 'high'], inplace=True)
    df['open_time'] = pd.to_datetime(df['open_time'], unit='s')

    df['hl2'] = ta.hl2(df['high'], df['low'])
    df['hma2'] = ta.wma(((ta.wma(df['hl2'], length=ma_period / 2 ) * 2) - ta.wma(df['hl2'], length=ma_period)), length=round(math.sqrt(ma_period)))

    return float(df[-1:]['hma2'].values[0])


def get_hma3(exchange=None, symbol=None, timeframe=None, ma_period=None, data=None):

    df = pd.DataFrame(data[:-1])
    df.drop(columns=['low', 'high'], inplace=True)
    df['open_time'] = pd.to_datetime(df['open_time'], unit='s')

    p = ma_period/2
    df['hma3'] = ta.wma( ((ta.wma(df['close'], length=p/3)*3) - ta.wma(df['close'], length=p/2) - ta.wma(df['close'], length=p)), p)

    return float(df[-1:]['hma3'].values[0])


def get_hma2_prev_bar(exchange=None, symbol=None, timeframe=None, ma_period=None, data=None):

    df = pd.DataFrame(data[:-1])
    #df.drop(columns=['low', 'high'], inplace=True)
    df['open_time'] = pd.to_datetime(df['open_time'], unit='s')

    df['hl2'] = ta.hl2(df['high'], df['low'])
    df['hma2'] = ta.wma(((ta.wma(df['hl2'], length=ma_period / 2 ) * 2) - ta.wma(df['hl2'], length=ma_period)), length=round(math.sqrt(ma_period)))

    return float(df[-2:]['hma2'].values[0])


def get_hma3_prev_bar(exchange=None, symbol=None, timeframe=None, ma_period=None, data=None):

    df = pd.DataFrame(data[:-1])
    df.drop(columns=['low', 'high'], inplace=True)
    df['open_time'] = pd.to_datetime(df['open_time'], unit='s')

    p = ma_period/2
    df['hma3'] = ta.wma( ((ta.wma(df['close'], length=p/3)*3) - ta.wma(df['close'], length=p/2) - ta.wma(df['close'], length=p)), p)

    return float(df[-2:]['hma3'].values[0])


class Macd(bt.Indicator):
    lines = ('macd', 'signal', 'histo',)
    params = (('period_me1', 12), ('period_me2', 26), ('period_signal', 9),)

    def __init__(self):
        me1 = EMA(self.data, period=self.p.period_me1)
        me2 = EMA(self.data, period=self.p.period_me2)
        self.l.macd = me1 - me2
        self.l.signal = EMA(self.l.macd, period=self.p.period_signal)
        self.l.histo = self.l.macd - self.l.signal

class Hma2(bt.Indicator):
    lines = ('hma2',)

    params = (('period_ma', 9),)

    # plotlines = {'hma2': dict(ls='--', color='blue')}
    plotinfo = hma2=dict(plot=True, subplot=False, plotlinelabels=False, plotabove=False)
    # plotlines = dict(hma2=dict(color='orange', ls='') )
    plotlines = dict(hma2=dict(_plotskip=False, color='green'))

    def __init__(self):
        # wma1 = WMA(self.datas[0].hl2, period=int(self.p.period_ma / 2)) * 2
        wma1 = WMA((self.datas[0].high + self.datas[0].low) / 2, period=int(self.p.period_ma / 2)) * 2
        # wma2 = WMA(self.datas[0].hl2, period=self.p.period_ma)
        wma2 = WMA((self.datas[0].high + self.datas[0].low) / 2, period=self.p.period_ma)
        wma1_2 = wma1 - wma2
        self.l.hma2 = WMA(wma1_2, period=round(math.sqrt(self.p.period_ma)))

class Hma3(bt.Indicator):
    lines = ('hma3',)
    params = (('period_ma', 9),)

    plotinfo = hma3=dict(plot=True, subplot=False, plotlinelabels=False, plotabove=False)
    plotlines = dict(hma3=dict(_plotskip=False, color='purple'))

    def __init__(self):
        p = int(self.p.period_ma / 2)

        wma1 = WMA(self.datas[0].close, period=int(p / 3)) * 3
        wma2 = WMA(self.datas[0].close, period=int(p / 2))
        wma3 = WMA(self.datas[0].close, period=p)
        wma1_2_3 = wma1 - wma2 - wma3
        self.l.hma3 = WMA(wma1_2_3, period=p)

class Hma_high(bt.Indicator):
    lines = ('hma_high',)

    params = (('period', 27),)

    plotinfo = hma_high=dict(plot=True, subplot=False, plotlinelabels=False, plotabove=False)
    plotlines = dict(hma_high=dict(_plotskip=False, color='green'))

    def __init__(self):
        wma1 = WMA(self.datas[0].high, period=int(self.p.period / 2)) * 2
        wma2 = WMA(self.datas[0].high, period=self.p.period)
        wma1_2 = wma1 - wma2
        self.l.hma_high = WMA(wma1_2, period=round(math.sqrt(self.p.period)))

def get_hma_high(exchange=None, symbol=None, timeframe=None, period=None, data=None):

    #print('Inicio funcion get_hma_high')
    #df = pd.DataFrame(data[:-1])
    df = pd.DataFrame(data)
    #df = data
    df['open_time'] = pd.to_datetime(df['open_time'], unit='s')
    #print(df)
    #p = period / 2
    df['hma_high'] = ta.wma(((ta.wma(df['high'], length=period / 2 ) * 2) - ta.wma(df['high'], length=period)), length=round(math.sqrt(period)))
    #print(df['hma_high'])
    #return float(df[-1:]['hma_high'].values[0])
    return df['hma_high']
    #return float(df[-1:]['hma_high'].values[0])

class Hma_low(bt.Indicator):
    lines = ('hma_low',)

    params = (('period', 27),)

    plotinfo = hma_low=dict(plot=True, subplot=False, plotlinelabels=False, plotabove=False)
    plotlines = dict(hma_low=dict(_plotskip=False, color='green'))

    def __init__(self):
        wma1 = WMA(self.datas[0].low, period=int(self.p.period / 2)) * 2
        wma2 = WMA(self.datas[0].low, period=self.p.period)
        wma1_2 = wma1 - wma2
        self.l.hma_low = WMA(wma1_2, period=round(math.sqrt(self.p.period)))

def get_hma_low(exchange=None, symbol=None, timeframe=None, period=None, data=None):

    #df = pd.DataFrame(data[:-1])
    df = pd.DataFrame(data)
    #df = data
    df['open_time'] = pd.to_datetime(df['open_time'], unit='s')

    #p = period / 2
    df['hma_low'] = ta.wma(((ta.wma(df['low'], length=period / 2 ) * 2) - ta.wma(df['low'], length=period)), length=round(math.sqrt(period)))

    #return float(df[-1:]['hma_low'].values[0])
    return df['hma_low']
    #return float(df[-1:]['hma_low'].values[0])


def recalculate_hl2(data=None):

    df = pd.DataFrame(data)
    # print(df)
    df.drop(columns=['hl2'], inplace=True)
    df['hl2'] = ta.hl2(df['high'], df['low'])

    # print(df)
    return df


#class Supertrend_poxy(bt.Indicator):
#    lines = ('supertrend',)
#    params = (('period', 7),('multiplier', 3))
#
#    plotinfo = supertrend=dict(plot=True, subplot=False, plotlinelabels=False, plotabove=False)
#    plotlines = dict(supertrend=dict(_plotskip=False, color='green'))
#
#    def __init__(self):
#        df = pd.DataFrame(self.datas)
#        #print(self.datas[0].close)
#        #self.l.supertrend = df.ta.supertrend(length = self.p.period, multiplier = self.p.multiplier)
#        #self.l.supertrend = ta.supertrend(self.datas[0].high, self.datas[0].low, self.datas[0].close, 7, 3)


#def get_supertrend(exchange=None, symbol=None, timeframe=None, length=7, multiplier=3, data=None):
def get_supertrend(data=None, length=7, multiplier=3):

    #df = pd.DataFrame(data)
    df = data
    #df['open_time'] = pd.to_datetime(df['open_time'], unit='s')
    #print(df)
    #df['hl2'] = ta.hl2(df['high'], df['low'])
    #df['hma2'] = ta.wma(((ta.wma(df['hl2'], length=ma_period / 2 ) * 2) - ta.wma(df['hl2'], length=ma_period)), length=round(math.sqrt(ma_period)))
    #self.l.supertrend = ta.supertrend(high = df['high'], low = df['low'], close = df['close'], length = period, multiplier = multiplier)

    df_ST = ta.supertrend(df['high'], df['low'], df['close'], 10, 1, 0)
    df['trend'] = df_ST['SUPERT_10_1.0']
    df['dir'] = df_ST['SUPERTd_10_1.0']
    df['long'] = df_ST['SUPERTl_10_1.0']
    df['short'] = df_ST['SUPERTs_10_1.0']

    #df['datetime'] = pd.to_datetime(df.datetime, unit='s')
    #print(df)
    #df.drop(columns=['volume'], inplace=True)
    #print(df.to_string())
    #print(df['high'], ' ', df['low'], ' ', df['open'], ' ', df['close'], ' ', df['hl2'], ' ', df['trend'], ' ', df['dir'], ' ', df['long'], ' ', df['short'])
    return float(df[-1:]['trend'].values[0])




class SuperTrendBand(bt.Indicator):
    """
    Helper inidcator for Supertrend indicator
    """
    params = (('period',7),('multiplier',3))
    lines = ('basic_ub','basic_lb','final_ub','final_lb')

    def __init__(self):
        self.atr = bt.indicators.AverageTrueRange(period=self.p.period)
        self.l.basic_ub = ((self.data.high + self.data.low) / 2) + (self.atr * self.p.multiplier)
        self.l.basic_lb = ((self.data.high + self.data.low) / 2) - (self.atr * self.p.multiplier)


    def next(self):
        if len(self)-1 == self.p.period:
            self.l.final_ub[0] = self.l.basic_ub[0]
            self.l.final_lb[0] = self.l.basic_lb[0]
        else:
            if self.l.basic_ub[0] < self.l.final_ub[-1] or self.data.close[-1] > self.l.final_ub[-1]:
                self.l.final_ub[0] = self.l.basic_ub[0]
            else:
                self.l.final_ub[0] = self.l.final_ub[-1]

            if self.l.basic_lb[0] > self.l.final_lb[-1] or self.data.close[-1] < self.l.final_lb[-1]:
                self.l.final_lb[0] = self.l.basic_lb[0]
            else:
                self.l.final_lb[0] = self.l.final_lb[-1]

class Supertrend(bt.Indicator):
    """
    Super Trend indicator
    """
    params = (('period', 7), ('multiplier', 3))
    lines = ('super_trend', 'direction', 'upTrend', 'downTrend')

    plotinfo = super_trend=dict(plot=True, subplot=False, plotlinelabels=False, plotabove=False)
    plotlines = dict(super_trend=dict(_plotskip=False, color='green'))

    def __init__(self):
        self.stb = SuperTrendBand(period = self.p.period, multiplier = self.p.multiplier)


    def next(self):
        if len(self) - 1 == self.p.period:
            self.l.super_trend[0] = self.stb.final_ub[0]
            return

        ##Direction
        self.l.direction[0] = 1
        if self.l.super_trend[-1] == self.stb.final_ub[-1]:
            if self.data.close[0] > self.stb.final_ub[0]:
               self.l.direction[0] = 1
            else:
                self.l.direction[0] = -1
        elif self.data.close[0] < self.stb.final_lb[0]:
            self.l.direction[0] = -1
        else:
            self.l.direction[0] = 1

        ##Flag
        if self.l.direction[0] > 0:
            self.l.upTrend[0] = True
            self.l.downTrend[0] = False
        else:
            self.l.upTrend[0] = False
            self.l.downTrend[0] = True

        if self.l.direction[0] == 1:
            self.l.super_trend[0] = self.stb.final_lb[0]
        else:
            self.l.super_trend[0] = self.stb.final_ub[0]
        #print(self.data.datetime.datetime(0).strftime('%Y-%m-%d %H:%M:%S'), '', self.data.high[0], '', self.data.low[0], '', self.data.open[0], '', self.data.close[0], '', self.data.hl2[0], '  ', self.l.super_trend[0], '  ', self.l.direction[0], ' ', self.l.upTrend[0], ' ', self.l.downTrend[0])


class SSLChannel(bt.Indicator):
    lines = ('ssld', 'sslu', 'hlv')
    params = (('period', 17),)
    plotinfo = dict(
        plot=True,
        plotname='SSL Channel',
        subplot=False,
        plotlinelabels=True)

    def _plotlabel(self):
        return [self.p.period]

    def __init__(self):
        #self.ma_lo = bt.indicators.HullMovingAverage(self.data.low, period=self.p.period)
        self.ma_lo = bt.indicators.SMA(self.data.low, period=self.p.period)
        #self.ma_hi = bt.indicators.HullMovingAverage(self.data.high, period=self.p.period)
        self.ma_hi = bt.indicators.SMA(self.data.high, period=self.p.period)

    def next(self):
        if self.data.close[0] > self.ma_hi[0]:
            self.l.hlv[0] = 1
        elif self.data.close[0] < self.ma_lo[0]:
            self.l.hlv[0] = -1
        else:
            self.l.hlv[0] = self.l.hlv[-1]

        if self.l.hlv[0] == -1:
            self.lines.ssld[0] = self.ma_hi[0]
            self.lines.sslu[0] = self.ma_lo[0]
        elif self.l.hlv[0] == 1:
            self.lines.ssld[0] = self.ma_lo[0]
            self.lines.sslu[0] = self.ma_hi[0]

        #print(self.data0.datetime.datetime(0).strftime('%Y-%m-%d %H:%M:%S'), '', self.data.high[0], '', self.data.low[0], '', self.data.open[0], '', self.data.close[0], '', self.ma_hi[0], '  ', self.ma_lo[0])


def get_ssl(exchange=None, symbol=None, timeframe=None, period=None, data=None):

    #df = data
    #df['open_time'] = pd.to_datetime(df['open_time'], unit='s')
    #print(df)
    #df['hl2'] = ta.hl2(df['high'], df['low'])
    #df['hma2'] = ta.wma(((ta.wma(df['hl2'], length=ma_period / 2 ) * 2) - ta.wma(df['hl2'], length=ma_period)), length=round(math.sqrt(ma_period)))
    #self.l.supertrend = ta.supertrend(high = df['high'], low = df['low'], close = df['close'], length = period, multiplier = multiplier)
    df = pd.DataFrame(data[:-1])

    #print('Inicio funcion get_ssl')
    #hma_hi = get_hma_high(period=period, data=data)
    #hma_lo = get_hma_low(period=period, data=data)

    #print(hma_hi)
    #print(hma_lo)

    #print('Close: ', df['close'].values[0])


    if df['close'].values[0] > hma_hi:
        hlv = 1
    elif df['close'].values[0] < hma_lo:
        hlv = -1
    #else:
    #    hlv[0] = hlv[-1]
    if hlv == -1:
        ssld = hma_hi
        sslu = hma_lo
    elif hlv == 1:
        ssld = hma_lo
        sslu = hma_hi


    df['sslu'] = sslu
    df['ssld'] = ssld


    #df['datetime'] = pd.to_datetime(df.datetime, unit='s')
    #print(df)
    #df.drop(columns=['volume'], inplace=True)
    #print(df.to_string())
    #print(df['high'], ' ', df['low'], ' ', df['open'], ' ', df['close'], ' ', df['hl2'], ' ', df['trend'], ' ', df['dir'], ' ', df['long'], ' ', df['short'])
    return float(df[-1:]['sslu'].values[0])


#def SSLChannels(dataframe, length=10, mode="hma"):
def SSLChannels(exchange=None, symbol=None, timeframe=None, period=None, data=None):
    """
    Source: https://www.tradingview.com/script/xzIoaIJC-SSL-channel/
    Author: xmatthias
    Pinescript Author: ErwinBeckers
    SSL Channels.
    Average over highs and lows form a channel - lines "flip" when close crosses
    either of the 2 lines.
    Trading ideas:
        * Channel cross
        * as confirmation based on up > down for long
    Usage:
        dataframe['sslDown'], dataframe['sslUp'] = SSLChannels(dataframe, 10)
    """
    #if mode not in ("hma"):
    #    raise ValueError(f"Mode {mode} not supported yet")

    #df = dataframe.copy()
    #df = pd.DataFrame(data[:-1])
    df = pd.DataFrame(data)

    #df['open_time'] = pd.to_datetime(df['open_time'], unit='s')
    #df['open_time'] = df_tmp['open_time'].apply(lambda x: datetime.fromtimestamp(x))
    #df = df.rename(columns={"open_time": "datetime"})
    #df['open_time'] = df['datetime'].apply(lambda timestamp: datetime.fromtimestamp(timestamp))
    #df['open_time'] = df['datetime'].apply(lambda x: datetime.fromtimestamp(x))
    #print(df)
    #df['date_time'] = [datetime.fromtimestamp(x) for x in df.open_time]
    #df['open_time'] = pd.to_datetime(df['open_time'], unit='s')
    #df['open_time'].map(lambda x: pd.to_datetime(x, yearfirst=True).tz_convert('America/Argentina/Buenos_Aires'))
    #print(df['open_time'].dt.tz_localize(tz='America/Argentina/Buenos_Aires'))
    #df = df.tz_convert(tz = 'America/Argentina/Buenos_Aires')
    #df['open_time'] = df['open_time'].dt.tz_convert('America/Argentina/Buenos_Aires')
    #print(df)

    #df['open_time'] = datetime.fromtimestamp(df['open_time'])
    #df.drop(columns=['datetime'], inplace=True)

    #df['open_time'] = pd.to_datetime(df['open_time'], unit='s')

    #if mode == "hma":
        #df["smaHigh"] = df["high"].rolling(length).mean()
        #df["smaLow"] = df["low"].rolling(length).mean()
    #df['hma_hi'] = get_hma_high(period=period, data=data)
    #df['hma_lo'] = get_hma_low(period=period, data=data)
    df['ma_hi'] = get_sma_high(period=period, data=df)
    df['ma_lo'] = get_sma_low(period=period, data=df)

    df["hlv"] = np.where(
        df["close"] > df["ma_hi"], 1, np.where(df["close"] < df["ma_lo"], -1, np.NAN)
    )
    df["hlv"] = df["hlv"].ffill()

    df["sslDown"] = np.where(df["hlv"] < 0, df["ma_hi"], df["ma_lo"])
    df["sslUp"] = np.where(df["hlv"] < 0, df["ma_lo"], df["ma_hi"])

    df.drop(columns=['ma_hi', 'ma_lo', 'hlv', 'sma_high', 'sma_low'], inplace=True)

    #return df["sslDown"], df["sslUp"]
    return df
