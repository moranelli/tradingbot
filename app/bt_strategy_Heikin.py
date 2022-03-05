import datetime, time  # For datetime objects
from time import strftime, gmtime
import pytz
import math
import os.path  # To manage paths
import sys  # To find out the script name (in argv[0])
projectPath = os.path.abspath(os.path.join(os.getcwd()))
sys.path.append(projectPath)

# Import the backtrader platform
import pandas as pd
import pandas_ta as ta
import backtrader as bt
from backtrader.feeds import GenericCSVData
# import backtrader.plot
import brokers
from brokers.bybit_exchange import get_exchange, get_info_symbol
from scripts.indicators import get_atr, get_rsi, get_ema, get_sma, get_wma, get_hma2, get_hma3, get_hma2_prev_bar,get_hma3_prev_bar, Macd, Hma2, Hma3
from scripts.heikin_ashi import heikin_ashi

# import matplotlib
# import matplotlib.pyplot as plt
# from matplotlib.path import Path
# from matplotlib.patches import PathPatch
# matplotlib.use('Qt5Agg')
# plt.switch_backend('Qt5Agg')


# import backtrader.plot
# import matplotlib as plt
# matplotlib.use('agg')
# plt.switch_backend('agg')

# import IPython

# import backtrader.plot
# import matplotlib
# matplotlib.use('nbagg')


class CustomCSV(GenericCSVData):
    lines = ('hl2',)
    
    params = (
        ('dtformat', '%Y-%m-%d %H:%M:%S'),
        ('tmformat', '%H:%M:%S.%f'),
        ('datetime', 0),
        ('time', -1),
        ('high', 1),
        ('low', 2),
        ('open', 3),
        ('close', 4),
        ('volume', 5),
        ('hl2', 6),        
        ('openinterest', -1),
    )
    
class PandasData(bt.feeds.PandasData):
    lines = ('hl2',)
    params = (
        ('dtformat', '%Y-%m-%d %H:%M:%S'),
        ('tmformat', '%H:%M:%S.%f'),
        ('datetime', None),
        ('time', -1),
        ('high', 'high'),
        ('low', 'low'),
        ('open', 'open'),
        ('close', 'close'),
        ('volume', 'volume'),
        ('hl2', 'hl2'),        
        ('openinterest', -1),
    )
    
# Create a Stratey
class TestStrategy(bt.Strategy):
    
    EXCHANGE_NAME = 'bybit'
    exchange = get_exchange()
    symbol = "BNBUSDT"
    timeframe = 5
    current_time_utc = datetime.datetime.now().timestamp()
    bar_number = 0
    info_symbol = ""
    
    entry_price = 0.0
    risk = 0.0
    risk_capital = 0.0
    StopLoss = 0.0
    TakeProfit = 0.0
    quantity = 0.0
    position_size = 0.0
    leverage = 0
    comision_maker = -0.025
    comision_taker =  0.075
    comision_open_position = 0.0
    comision_close_position = 0.0
    comisions = 0.0
    total_gross_profit = 0.0
    total_gross_loss = 0.0
    profit_factor = 0.0

    last_position = ""
    result_position = ""
    cant_position = 0
    cant_long_position = 0
    cant_short_position = 0
    cant_long_win_position = 0
    cant_long_loss_position = 0
    cant_short_win_position = 0
    cant_short_loss_position = 0
    efectividad_long = 0
    efectividad_short = 0
    efectividad = 0
    
    SL_ATRlen = 0.0
    sl_atr = 0.0
    reward_ratio = 0.0
    
    params = (
        ('fast_ma_period', 14),
        ('slow_ma_period', 54),
        ('SL_ATRlen', 13),
        ('sl_atr', 15), #Se divide por 10 para obtener valor con decimales. Ej: 9 - 0.9
        ('reward_ratio', 13),  #Se divide por 10 para obtener valor con decimales. Ej: 13 - 1.3
        ('risk_perc', 4.0),
        ('printlog', False),
    )
    
    if(info_symbol == ""):
        info_symbol = get_info_symbol(exchange=exchange, symbol=symbol, info_symbol=info_symbol)

    def log(self, txt, dt=None, doprint=True, printtime=True, tofile=False):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.datetime(0).strftime('%Y-%m-%d_%H:%M:%S')
        if self.params.printlog or doprint:
            if printtime:                
                print('%s - %s, %s' % (self.bar_number, dt, txt))
            else:
                print('%s' % (txt))
        if tofile:
            with open("data/backtrader_strategy.csv", "a") as outfile:
                outfile.write(txt +'\n')

    def __init__(self):
        
        for i, d in enumerate(self.datas):
            if d._name == 'Real':
                self.real = d
            elif d._name == 'Heikin':
                self.hk = d

        # Keep a reference to the "close" line in the data[0] dataseries
        self.datadatetime = self.real.datetime.datetime(0).strftime('%Y-%m-%d_%H:%M:%S')
        # self.datahigh = self.real[0].high[0]
        self.datahigh = self.hk.high
        self.datalow = self.hk.low
        # self.dataopen = self.hk[0].open
        self.dataopen = self.real.open
        self.dataclose = self.hk.close
        # self.datahl2 = self.hk[0].hl2
        self.datahl2 = (self.hk.high + self.hk.low) / 2
        self.sl_atr = float(self.params.sl_atr / 10)
        self.reward_ratio = float(self.params.reward_ratio / 10)

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None

        # Add indicator
        self.slow_ma = bt.indicators.SMA(self.hk, period=self.params.slow_ma_period, plotname='slow_ma')
        self.fast_ma = bt.indicators.EMA(self.hk, period=self.params.fast_ma_period, plotname='fast_ma')
        self.atr = bt.indicators.ATR(self.hk, period=self.params.SL_ATRlen, plotname='atr', plotabove=False)

        # self.hma2 = Hma2(self.datas[0], plotname='hma2', subplot=False, plotabove=False)
        # self.hma2 = Hma2(self.datas[0], plotname='hma2')
        self.hma2 = Hma2(self.hk, plotname='hma2')
        self.hma3 = Hma3(self.hk, plotname='hma3')
        self.hullcrossover = bt.indicators.CrossOver(self.hma2, self.hma3, plot=False)
        self.hullcrossunder = bt.indicators.CrossOver(self.hma3, self.hma2, plot=False)
        
    def notify_order(self, order):
    #     time.sleep(0)

    # def create_order(self, order):
    # def create_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        # if order.status in [order.Completed]:
        if order.status in [order.Completed, order.Submitted, order.Accepted]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Size: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.size,
                     order.executed.comm))

                self.buyprice = order.executed.price
                # self.buyprice = self.entry_price
                self.positionsize = order.executed.value
                # self.positionsize = self.position_size
                # self.buycomm = order.executed.comm
                # self.opsize = order.executed.size
                self.loss = self.positionsize * (self.params.risk_perc / 100)
                # self.comision_open_position = self.positionsize * self.comision_maker * self.leverage
                # self.comision_open_position = self.positionsize * self.comision_maker
                # self.comision_open_position = (self.position_size * self.comision_maker) / 100
                self.comision_open_position = (self.position_size * self.comision_maker) / 100
                
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Size: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.size,
                          order.executed.comm))
                
                self.buyprice = order.executed.price
                # self.buyprice = self.entry_price
                self.positionsize = order.executed.value
                # self.positionsize = self.position_size
                # self.buycomm = order.executed.comm
                # self.opsize = order.executed.size
                self.loss = self.positionsize * (self.params.risk_perc / 100)
                # self.comision_open_position = self.positionsize * self.comision_maker * self.leverage
                self.comision_open_position = (self.position_size * self.comision_maker) / 100

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')
            
        # self.check_exit_position()

        # Write down: no pending order
        self.order = None

    # def notify_trade(self, trade):
    #     time.sleep(0)
        
    def notify_trade(self, trade):
    # def exit_trade(self):
        if not trade.isclosed:
            return
        
        # self.cant_position += 1
        
        if self.result_position == "win":
            gross_pnl = self.loss * self.reward_ratio
            # self.comision_close_position = ((self.positionsize + gross_pnl) * self.comision_maker) * self.leverage
            # self.comision_close_position = ((self.positionsize + gross_pnl) * self.comision_maker) / 100
            # self.comision_close_position = ((self.position_size + gross_pnl) * self.comision_maker) / 100
            self.comision_close_position = ((self.quantity * self.TakeProfit) * self.comision_maker) / 100
            # net_pnl = gross_pnl - self.comision_close_position
            self.total_gross_profit += gross_pnl
        else:
            # gross_pnl = (trade.price - self.buyprice) * self.opsize
            gross_pnl = -self.loss
            # self.comision_close_position = ((self.positionsize - self.loss) * self.comision_taker) * self.leverage
            # self.comision_close_position = ((self.positionsize - self.loss) * self.comision_taker) / 100
            # self.comision_close_position = ((self.position_size - self.loss) * self.comision_taker) / 100
            self.comision_close_position = ((self.quantity * self.StopLoss) * self.comision_taker) / 100
            # net_pnl = gross_pnl - (trade.commission * self.leverage)
            # net_pnl = gross_pnl - self.comision_close_position
            self.total_gross_loss += gross_pnl
            
        net_pnl = gross_pnl - self.comision_open_position - self.comision_close_position
        self.comisions += self.comision_open_position - self.comision_close_position


        # self.log('gross_pnl: %.2f, trade.price: %.2f self.buyprice: %.2f, self.positionsize: %.2f, self.opsize: %.2f, leverage: %.2f, size*leverage: %.2f, net_pnl: %.2f, self.buycomm: %.2f. trade.commission: %.2f '%
        #                  (gross_pnl, trade.price, self.buyprice, self.positionsize, self.opsize, self.leverage, self.opsize*self.leverage, net_pnl, self.buycomm, trade.commission))
        # self.log('gross_pnl: %.2f, trade.price: %.2f self.buyprice: %.2f, StopLoss: %.2f, TakeProfit: %.2f, risk_capital: %.2f, self.positionsize: %.2f, self.opsize: %.2f, self.position_size: %.2f, quantity: %.2f, leverage: %.2f, net_pnl: %.2f, comision_open_position: %.2f, , comision_close_position: %.2f'%
        #                  (gross_pnl, trade.price, self.buyprice, self.StopLoss, self.TakeProfit, self.risk_capital, self.positionsize, self.opsize, self.position_size, self.quantity, self.leverage, net_pnl, self.comision_open_position, self.comision_close_position))
        self.log('gross_pnl: %.2f, self.buyprice: %.2f, StopLoss: %.2f, TakeProfit: %.2f, risk_capital: %.2f, self.positionsize: %.2f, self.position_size: %.2f, quantity: %.2f, leverage: %.2f, net_pnl: %.2f, comision_open_position: %.2f, comision_close_position: %.2f'%
                         (gross_pnl, self.buyprice, self.StopLoss, self.TakeProfit, self.risk_capital, self.positionsize, self.position_size, self.quantity, self.leverage, net_pnl, self.comision_open_position, self.comision_close_position))
        # print('net_pnl: %.2f '% (net_pnl))
        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                         (gross_pnl, net_pnl))
        
        self.broker.add_cash(net_pnl)

    
        # self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
        #          (trade.pnl, trade.pnlcomm))
        
        
    # def next(self):
    #     self.log('{} next, open {} close {}'.format(
    #         self.data.datetime.date(),
    #         self.data.open[0], self.data.close[0])
    #     )
    
    def next(self):
        self.log('%f, %f, %f, %f, %f' % (
            self.hk.high[0], self.hk.low[0], self.hk.open[0], self.hk.close[0], (self.hk.high[0] + self.hk.low[0]) / 2), doprint=False, printtime=True, tofile=False)
        # self.log('%s %f %f %f %f %f' % (self.datadatetime, self.datahigh[0], self.datalow[0], self.dataopen[0], self.dataclose[0], self.datahl2[0]), doprint=True, printtime=True, tofile=False)
       
        time.sleep(0)
        
        # self.check_exit_position()

    def next_open(self):
    # def next(self):
        # Simply log the closing price of the series from the reference
        # self.log('High: %.2f - Low: %.2f - Open: %.2f - Close: %.2f - HL2: %.2f ATR: %.10f - fast_ma: %.2f - slow_ma: %.2f - CrossFastOverSlow: %s - HMA2: %.2f - HMA3: %.2f - self.hullcrossover: %s' % (self.datahigh[0], self.datalow[0], self.dataopen[0], self.dataclose[0], self.datahl2[0], self.atr[0], self.fast_ma[0], self.slow_ma[0], self.fast_ma[0] >= self.slow_ma[0], self.hma2[0], self.hma3[0], self.hullcrossover[0] > 0), doprint=True)
        
        # self.log('Next Open %0.2f, %0.2f, %0.2f, %0.2f' % (
        #     self.data.open[0], self.data.high[0], self.data.low[0],
        #     self.data.close[0]))
        # self.check_exit_position()        
        self.bar_number += 1
        
        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        # Check if we are in the market
        if not self.position:
            # LONG
            if self.hullcrossunder[0] > 0 and self.fast_ma[0] >= self.slow_ma[0]: # Fast ma crosses above slow ma
            # if self.hullcrossunder[-1] > 0 and self.fast_ma[-1] >= self.slow_ma[-1]: # Fast ma crosses above slow ma
            # if self.hullcrossunder[1] > 0 and self.fast_ma[1] >= self.slow_ma[1]: # Fast ma crosses above slow ma
                
                # self.entry_price = self.dataclose[0]
                self.entry_price = self.dataopen[0]
                balance_details_size = self.broker.getvalue() * 0.95
                # SL_ret = self.entry_price - (self.atr[0] * self.sl_atr)
                SL_ret = self.entry_price - (self.atr[-1] * self.sl_atr)
                # SL_ret = self.entry_price - (self.atr[1] * self.sl_atr)
                # self.StopLoss = float("{:0.0{}f}".format(float(min(SL_ret, self.datalow[0] - (self.atr[0] * 0.2))), self.info_symbol['pricePrecision']))
                self.StopLoss = float("{:0.0{}f}".format(float(min(SL_ret, self.datalow[-1] - (self.atr[-1] * 0.2))), self.info_symbol['pricePrecision']))
                # self.StopLoss = float("{:0.0{}f}".format(float(min(SL_ret, self.datalow[1] - (self.atr[1] * 0.2))), self.info_symbol['pricePrecision']))
                self.TakeProfit = self.entry_price + (abs(self.entry_price - self.StopLoss) * self.reward_ratio)
                self.TakeProfit = float("{:0.0{}f}".format(float(self.TakeProfit), self.info_symbol['pricePrecision']))
        
                self.risk = self.params.risk_perc / 100
                self.risk_capital = self.risk * balance_details_size
                self.quantity = float("{:0.0{}f}".format(float(self.risk_capital / abs(self.entry_price - self.StopLoss)), self.info_symbol['quantityPrecision']))
                self.position_size = self.quantity * self.entry_price
                self.leverage = math.ceil(self.position_size / balance_details_size)

                # BUY, BUY, BUY!!! (with all possible default parameters)
                self.log('LONG CREATE, %.2f' % self.entry_price)

                # self.broker.setcommission(commission=0.1, margin=2000, mult=self.leverage)
                
                # Keep track of the created order to avoid a 2nd order
                # self.order = self.buy(exectype=bt.Order.Limit, price=self.entry_price, size=self.position_size)
                self.order = self.buy(exectype=bt.Order.Limit, price=self.entry_price)
                self.last_position = "long"
                # self.create_order(self.order)
            
            # SHORT
            elif self.hullcrossover[0] > 0 and self.fast_ma[0] < self.slow_ma[0]:
            # elif self.hullcrossover[-1] > 0 and self.fast_ma[-1] < self.slow_ma[-1]:
            # elif self.hullcrossover[1] > 0 and self.fast_ma[1] < self.slow_ma[1]:
                # SELL, SELL, SELL!!! (with all possible default parameters)
                
                # self.entry_price = self.dataclose[0]
                self.entry_price = self.dataopen[0]
                balance_details_size = self.broker.getvalue() * 0.95
                # SL_ret = self.entry_price + (self.atr[0] * self.sl_atr)
                SL_ret = self.entry_price + (self.atr[0] * self.sl_atr)
                # SL_ret = self.entry_price + (self.atr[1] * self.sl_atr)
                self.StopLoss = float("{:0.0{}f}".format(float(max(SL_ret, self.datahigh[-1] + (self.atr[0] * 0.2))), self.info_symbol['pricePrecision']))
                # self.StopLoss = float("{:0.0{}f}".format(float(max(SL_ret, self.datahigh[-1] + (self.atr[-1] * 0.2))), self.info_symbol['pricePrecision']))
                self.TakeProfit = self.entry_price - (abs(self.entry_price - self.StopLoss) * self.reward_ratio)
                self.TakeProfit = float("{:0.0{}f}".format(float(self.TakeProfit), self.info_symbol['pricePrecision']))
                
                self.risk = self.params.risk_perc / 100
                self.risk_capital = self.risk * balance_details_size
                self.quantity = float("{:0.0{}f}".format(float(self.risk_capital / abs(self.entry_price - self.StopLoss)), self.info_symbol['quantityPrecision']))
                self.position_size = self.quantity * self.entry_price
                self.leverage = math.ceil(self.position_size / balance_details_size)                
                
                self.log('SHORT CREATE, %.2f' % self.entry_price)
                
                # Keep track of the created order to avoid a 2nd order
                # self.order = self.sell(exectype=bt.Order.Limit, price=self.entry_price, size=self.position_size)
                self.order = self.sell(exectype=bt.Order.Limit, price=self.entry_price)
                self.last_position = "short"
                # self.create_order(self.order)
        
        self.check_exit_position()
            

    def check_exit_position(self):
        if self.position:
            if self.last_position == "long":
                if self.datahigh[0] >= self.TakeProfit:
                # if self.datahigh[-1] >= self.TakeProfit:
                    # self.log(f'CLOSE LONG PROFIT {self.dataclose[0]:2f}')
                    self.log(f'CLOSE LONG PROFIT {self.TakeProfit:2f}')
                    self.order = self.close(exectype=bt.Order.Limit, price=self.TakeProfit)
                    self.result_position = "win"
                    # self.cant_long_position += 1
                    self.cant_long_win_position += 1
                    # self.exit_trade()
                elif self.datalow[0] <= self.StopLoss:
                # elif self.datalow[-1] <= self.StopLoss:
                    # self.log(f'CLOSE LONG LOSS {self.dataclose[0]:2f}')
                    self.log(f'CLOSE LONG LOSS {self.StopLoss:2f}')
                    self.order = self.close(exectype=bt.Order.StopLimit, price=self.StopLoss)
                    self.result_position = "loss"
                    # self.cant_long_position += 1
                    self.cant_long_loss_position += 1
                    # self.exit_trade()
                    
            elif self.last_position == "short":
                if self.datalow[0] <= self.TakeProfit:
                # if self.datalow[-1] <= self.TakeProfit:
                    # self.log(f'CLOSE SHORT PROFIT {self.dataclose[0]:2f}')
                    self.log(f'CLOSE SHORT PROFIT {self.TakeProfit:2f}')
                    self.order = self.close(exectype=bt.Order.Limit, price=self.TakeProfit)
                    self.result_position = "win"
                    # self.cant_short_position += 1
                    self.cant_short_win_position += 1
                    # self.exit_trade()
                elif self.datahigh[0] >= self.StopLoss:
                # elif self.datahigh[-1] >= self.StopLoss:
                    # self.log(f'CLOSE SHORT LOSS {self.dataclose[0]:2f}')
                    self.log(f'CLOSE SHORT LOSS {self.StopLoss:2f}')
                    self.order = self.close(exectype=bt.Order.StopLimit, price=self.StopLoss)
                    self.result_position = "loss"
                    # self.cant_short_position += 1
                    self.cant_short_loss_position += 1
                    # self.exit_trade()

    def stop(self):
        self.cant_long_position = self.cant_long_win_position + self.cant_long_loss_position
        self.cant_short_position = self.cant_short_win_position + self.cant_short_loss_position
        self.cant_position = self.cant_long_position + self.cant_short_position
        if(self.cant_long_position != 0):
            self.efectividad_long = int((self.cant_long_win_position / self.cant_long_position) * 100)
        if(self.cant_short_position != 0):
            self.efectividad_short = int((self.cant_short_win_position / self.cant_short_position) * 100) 
        if(self.cant_position != 0):
            self.efectividad = int(((self.cant_long_win_position + self.cant_short_win_position) / self.cant_position) * 100)
        
        if(self.total_gross_loss != 0):    
            self.profit_factor = abs(self.total_gross_profit / self.total_gross_loss)
        else: 
            self.profit_factor = 1.0           

        # Filtro de impresion en pantalla
        # if(self.broker.getvalue() > 110 and self.efectividad >= 65 and self.efectividad_long >= 55 and self.efectividad_short >= 55):
        # if(self.broker.getvalue() > 130 and self.efectividad >= 75):
        if(1 == 1):
            self.log('fast_ma: %2d , slow_ma: %2d , SL_ARTlen: %2d , sl_atr: %.1f , reward_ratio: %.1f , Positions: %d , Pos Long: %d, Pos Short: %d, Efectividad: %d , Long: %d , Short: %d , Balance: %.2f , Comisiones: %.2f , Profit_Factor: %.2f' %
                 (self.params.fast_ma_period, self.params.slow_ma_period, self.params.SL_ATRlen, self.sl_atr, self.reward_ratio, self.cant_position, self.cant_long_position, self.cant_short_position, self.efectividad, self.efectividad_long, self.efectividad_short, self.broker.getvalue(), self.comisions, self.profit_factor), doprint=True, printtime=False, tofile=True)


# define custom commission scheme that reproduces Binance perpetual future trading
class CommInfo_BinancePerp(bt.CommInfoBase):
    params = (
      ('stocklike', False),  # Futures
      ('commtype', bt.CommInfoBase.COMM_PERC),  # Apply % Commission
    )

    def _getcommission(self, size, price, pseudoexec):
        return size * price * self.p.commission * self.p.mult

    def get_margin(self, price):
        return price / self.p.mult

    def getsize(self, price, cash):
        '''Returns fractional size for cash operation @price'''
        return self.p.mult * (cash / price)
    
class CryptoContractCommissionInfo(bt.CommissionInfo):
    '''Commission scheme for cryptocurrency contracts.
    
        Including futures contracts and perpetual swap contracts.
        
        Required Args:
            commission: commission fee in percentage, between 0.0 and 1.0
            mult: leverage, for example 10 means 10x leverage
    '''
    params = (
        ('stocklike', False),
        ('commtype', bt.CommInfoBase.COMM_PERC), # apply % commission
    )
    
    def __init__(self):
        assert abs(self.p.commission) < 1.0 # commission is a percentage
        assert self.p.mult >= 1.0
        assert self.p.margin is None
        assert self.p.commtype == bt.CommInfoBase.COMM_PERC
        assert not self.p.stocklike
        assert self.p.percabs
        assert self.p.leverage == 1.0
        self.p.automargin = 1 / self.p.mult

        super().__init__()

    def getsize(self, price, cash):
        '''Support fractional size.
        
            More details at https://www.backtrader.com/blog/posts/2019-08-29-fractional-sizes/fractional-sizes/.
        '''
        # return self.p.leverage * (cash / price)
        return self.p.mult * (cash / price)

    def _getcommission(self, size, price, pseudoexec):
        '''Percentage based commission fee.
        
            More details at https://www.backtrader.com/docu/user-defined-commissions/commission-schemes-subclassing/.
        '''
        return abs(size) * self.p.commission * price * self.p.mult
    
    
if __name__ == '__main__':
    
    df = pd.DataFrame(columns=['symbol', 'fast_ma', 'slow_ma', 'SL_ARTlen', 'sl_atr', 'reward_ratio', 'positions', 'win', 'loss', 'efectividad', 'balance'])
    
    # Create a cerebro entity
    cerebro = bt.Cerebro(cheat_on_open=True)
    
    # Add a strategy
    # strats = cerebro.optstrategy(
    #     TestStrategy,
    #     fast_ma_period=range(8, 27),
    #     slow_ma_period=range(34, 61),
    #     SL_ATRlen=range(8, 17),
    #     sl_atr=range(8, 16),
    #     reward_ratio=range(13, 14),
    #     )
    
    cerebro.addstrategy(TestStrategy)

    # Datas are in a subfolder of the samples. Need to find where the script is
    # because it could have been called from anywhere
    # modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
    # datapath = os.path.join(modpath, 'data/2021_3minutes.csv')
    # datapath = ('data/2021_3minutes.csv')
    # datapath = ('data/2021_3minutes_v2_prod.csv')
    # datapath = ('data/2021_15minutes_v2_testnet.csv')
    # datapath = ('data/2021_15minutes_v2_prod.csv')
    # datapath = ('data/BNBUSDT_2021_5minutes_sample_prod.csv')
    datapath = ('data/BNBUSDT_2021_5minutes_prod.csv')

    # Create a Data Feed
    fromdate = datetime.datetime.strptime('2021-08-16', '%Y-%m-%d')
    todate = datetime.datetime.strptime('2021-12-31', '%Y-%m-%d')
    # data = CustomCSV(dataname='data/2021_3minutes.csv', dtformat=('%Y-%m-%d %H:%M:%S'), timeframe=bt.TimeFrame.Minutes)
    # data = CustomCSV(dataname='data/2021_3minutes_v2_prod.csv', dtformat=('%Y-%m-%d %H:%M:%S'), timeframe=bt.TimeFrame.Minutes)
    # data = CustomCSV(dataname='data/2021_15minutes_v2_testnet.csv', dtformat=('%Y-%m-%d %H:%M:%S'), timeframe=bt.TimeFrame.Minutes)
    # data = CustomCSV(dataname='data/2021_15minutes_v2_prod.csv', dtformat=('%Y-%m-%d %H:%M:%S'), timeframe=bt.TimeFrame.Minutes)
    # data = CustomCSV(dataname='data/2021_3minutes_testnet.csv', dtformat=('%Y-%m-%d %H:%M:%S'), timeframe=bt.TimeFrame.Minutes)
    dataframe = pd.read_csv(datapath,
                                skiprows=0,
                                header=0,
                                parse_dates=True,
                                index_col='datetime')

    # print(dataframe)
    # data = bt.feeds.PandasData(dataname=dataframe, openinterest=-1)
    # data3 = bt.feeds.PandasData(dataname=dataframe, tz=pytz.timezone('America/Argentina/Buenos_Aires'))
    # data2 = PandasData(dataname=dataframe, tz=pytz.timezone('America/Argentina/Buenos_Aires'))
    real_data = PandasData(dataname=dataframe)

    # column_order_names = ["datetime", "high", "low", "open", "close", "volume"]
    # df = df.reindex(columns=column_order_names)
    heikin_ashi_df = heikin_ashi(dataframe)
    # print(heikin_ashi_df)
    # heikin_ashi_df = recalculate_hl2(heikin_ashi_df)
    # print(heikin_ashi_df)
    
    # print(heikin_ashi_df)
    # data3 = PandasData(dataname=heikin_ashi_df, tz=pytz.timezone('America/Argentina/Buenos_Aires'))
    heikin_data = PandasData(dataname=heikin_ashi_df)
    
    #Add the filter
    # data2.addfilter(bt.filters.HeikinAshi(data2))

    # Add the Data Feed to Cerebro
    cerebro.adddata(real_data, name="Real")
    cerebro.adddata(heikin_data, name="Heikin")

    # Set our desired cash start
    cerebro.broker.setcash(100.0)
    # cerebro.broker.set_shortcash(True)
    
    # Add a FixedSize sizer according to the stake
    cerebro.addsizer(bt.sizers.PercentSizer, percents=95)

    # Set the commission
    #cerebro.broker.setcommission(commission=0.00)
    
    # comminfo = CommInfo_BinancePerp(commission=0.00025, mult=binance_leverage, automargin=True)
    comminfo = CryptoContractCommissionInfo(commission=0.0, mult=1)    
    cerebro.broker.addcommissioninfo(comminfo)

    # Run over everything
    # cerebro.run(maxcpus=1)
    cerebro.run(preload=True, runonce=True, optreturn=True, optdatas=True)
    
    # cerebro.plot(style='candle', numfigs=1, barup ='lime', bardown ='red', valuetags=False)
    # cerebro.plot(height = 30, iplot = False)




