"""
Source: https://www.tradingview.com/script/xzIoaIJC-SSL-channel/
Author: dm21376
Hawk Strategy
Estrategia de traiding
"""

#### Imports ####
from datetime import datetime
import time
import math
import logging

import json
from brokers.bybit_exchange import check_orders, check_position, get_balance, set_leverage, create_order, cerrar_posiciones, cancelar_ordenes, get_ticker_with_queue, check_position_with_queue, get_position_with_queue, get_order_with_queue, check_order_with_queue, obtener_kline_symbol
#from scripts.telegrambot import telegram_bot_sendtext
from scripts.indicators import get_atr
from utils import log, errors
from config import bybit_config

## Declaracion de loggers ####
logger_position = log.setup_custom_logger('position', filename='log/bybit_position.log', console=True, log_level=logging.DEBUG)
logger_strategy = log.setup_custom_logger('strategy', filename='log/bybit_strategy.log', console=True, log_level=logging.DEBUG)


class Strategy():
    """Clase de estrategia de trading
    """

    def __init__(self, exchange=None, data=None, symbol=None, timeframe=None, info_symbol=None, wst=None):
        self.exchange = exchange
        self.data = data
        self.symbol = symbol
        self.timeframe = timeframe
        self.info_symbol = info_symbol
        self.wst = wst
        self.max_leverage = 30

    def strategy(self, num_retry):
        """Funcion de estrategia

        Args:
            num_retry ([type]): [description]
        """
        current_time_utc = datetime.now().timestamp()

        order_time = float(self.data['time'])
        order_price = float(self.data['strategy']['order_price'])
        bar_open_time_unix = self.data['bar']['bar_open_time']
        sl_atr_len = 8
        atr = get_atr(exchange=self.exchange, symbol=self.symbol, timeframe=self.timeframe, periods=sl_atr_len)
        order_action = self.data['strategy']['order_action']
        position_side = self.data['strategy']['position_side']
        order_prefix_id = self.data['strategy']['order_id']
        order_id = order_prefix_id + "-" +  str(bar_open_time_unix) + "-" + str(num_retry)
        order_id_tp = order_prefix_id + "_tp" + "-" +  str(bar_open_time_unix) + "-" + str(num_retry)

        order_type = "Limit"
        order_tp_type = "Limit"
        sl_atr = float(self.data['strategy']['sl_atr'])
        reward_ratio = float(self.data['strategy']['reward_ratio'])
        if position_side == 'long':
            side_sl_tp = 'Sell'
        else:
            side_sl_tp = 'Buy'

        risk_perc = 5.0

        #### Validar si existe una posicion abierta para el simbolo. ####

        # try:
        #     # if(check_position(exchange=exchange, symbol=SYMBOL, symbol_slash=SYMBOL_SLASH, reintentos=2, sleep=1) is True):
        #     if(check_position_with_queue(exchange=self.exchange, symbol=self.symbol, q_position=self.q_position, reintentos=2, sleep=1) is True):
        #         logger_strategy.error("Solo se permite una operacion a la vez.")
        #         return { "code": "error", "message": "Solo se permite una operacion a la vez." }
        # except (Exception) as e:
        #     return e

        ## Validacion de timestamp
        current_time_utc_for_validate_request = datetime.now()
        request_time = datetime.fromtimestamp(round(int(order_time) / 1000))
        request_time_diff = (current_time_utc_for_validate_request - request_time).total_seconds()
        if request_time_diff > bybit_config.RECVWINDOW:
            logger_strategy.error("Tiempo de request fuera de ventana permitida.")
            logger_strategy.error("current_time_utc_for_validate_request: " + str(current_time_utc_for_validate_request))
            logger_strategy.error("request_time: " + str(request_time))
            logger_strategy.error("request_time_diff: " + str(request_time_diff))
            return { "code": "error", "message": "Tiempo de request fuera de ventana permitida." }


        ## Calcular el stock y apalancamiento necesario para el % de riesgo configurado. (5% por defecto)
        try:
            balance = get_balance(exchange=self.exchange)
            if balance < 10:
                logger_strategy.error("El balance de la cuenta es < 10 USDT")
                return { "code": "error", "message": "El balance de la cuenta es < 10 USDT" }
        except (Exception) as exc:
            return exc


        ## Multiplico el balance para utilizar un 0.05% menos del portafolio
        balance_details_size = balance * 0.95

        ## Consulto precio actual del symbol. Luego se debe utilizar el precio de entrada de TradingView order_price
        ticker = get_ticker_with_queue(exchange=self.exchange, symbol=self.symbol, wst=self.wst)

        ## Valido si el order price tiene valor para crear la orden
        #order_price = (bid_price + ask_price) / 2
        if order_price is None:
            logger_strategy.error("No es posible obtener el precio del simbolo. Lista vacia.")
            return { "code": "error", "message": "No es posible obtener el precio del simbolo. Lista vacia." }

        ## Se obtiene el valor de low y high de la vela anterior para calcular el ATR
        kline_symbol = obtener_kline_symbol(exchange=self.exchange, symbol=self.symbol, timeframe=self.timeframe, time_from=current_time_utc, limit=2)[0]
        low_price_prev_bar = float("{:0.0{}f}".format(float(kline_symbol['low']), self.info_symbol['pricePrecision']))
        high_price_prev_bar = float("{:0.0{}f}".format(float(kline_symbol['high']), self.info_symbol['pricePrecision']))

        ## Se hace el calculo inicial de TP y SL dependiendo del tipo de posicion
        if position_side == 'long':
            # entry_price = order_price #* 1.0001
            entry_price = float("{:0.0{}f}".format(float(order_price), self.info_symbol['pricePrecision']))
            sl_ret = entry_price - (atr * sl_atr)
            stop_loss = float("{:0.0{}f}".format(float(min(sl_ret, low_price_prev_bar - (atr * 0.2))), self.info_symbol['pricePrecision']))
            take_profit = entry_price + (abs(entry_price - stop_loss) * reward_ratio)
            take_profit = float("{:0.0{}f}".format(float(take_profit), self.info_symbol['pricePrecision']))
        else:
            # entry_price = order_price #* 0.9999
            entry_price = float("{:0.0{}f}".format(float(order_price), self.info_symbol['pricePrecision']))
            sl_ret = entry_price + (atr * sl_atr)
            stop_loss = float("{:0.0{}f}".format(float(max(sl_ret, high_price_prev_bar + (atr * 0.2))), self.info_symbol['pricePrecision']))
            take_profit = entry_price - (abs(entry_price - stop_loss) * reward_ratio)
            take_profit = float("{:0.0{}f}".format(float(take_profit), self.info_symbol['pricePrecision']))

        risk = risk_perc / 100
        risk_capital = risk * balance_details_size
        quantity = float("{:0.0{}f}".format(float(risk_capital / abs(entry_price - stop_loss)), self.info_symbol['quantityPrecision']))
        position_size = quantity * entry_price
        leverage = math.ceil(position_size / balance_details_size)

        ## Logging d ela operacion a realizar
        logger_strategy.info("**************** DEBUG *****************")
        logger_strategy.info("order_id DEBUG: " + str(order_id))
        logger_strategy.info("order_id_tp DEBUG: " + str(order_id_tp))
        logger_strategy.info("entry_price DEBUG: " + str(entry_price))
        logger_strategy.info("atr DEBUG: " + str(atr))
        logger_strategy.info("sl_atr DEBUG: " + str(sl_atr))
        logger_strategy.info("sl_ret DEBUG: " + str(sl_ret))
        if position_side == 'long':
            logger_strategy.info("low_price_prev_bar DEBUG: " + str(low_price_prev_bar))
            logger_strategy.info("low_price_prev_bar - (atr * 0.2) DEBUG: " + str(low_price_prev_bar - (atr * 0.2)))
        else:
            logger_strategy.info("high_price_prev_bar DEBUG: " + str(high_price_prev_bar))
            logger_strategy.info("high_price_prev_bar + (atr * 0.2) DEBUG: " + str(high_price_prev_bar + (atr * 0.2)))
        logger_strategy.info("stop_loss DEBUG: " + str(stop_loss))
        logger_strategy.info("take_profit DEBUG: " + str(take_profit))
        logger_strategy.info("balance DEBUG: " + str(balance))
        logger_strategy.info("balance_details_size DEBUG: " + str(balance_details_size))
        logger_strategy.info("risk_perc DEBUG: " + str(risk_perc))
        logger_strategy.info("position_size DEBUG: " + str(position_size))
        logger_strategy.info("quantity DEBUG: " + str(quantity))
        logger_strategy.info("position_size / balance_details_size DEBUG: " + str(position_size / balance_details_size))
        logger_strategy.info("leverage DEBUG: " + str(leverage))
        logger_strategy.info("Total Profit DEBUG: " + str(risk_capital * reward_ratio))
        logger_strategy.info("Total Loss DEBUG: " + str(risk_capital))
        logger_strategy.info("**************** DEBUG *****************")

        #### Valido si el leverage es mayor que el maximo permitido por la estrategia ####
        try:
            if leverage > self.max_leverage:
                logger_strategy.info("El apalancamiento supera el maximo permitido.")
                raise errors.OrderError({ "code": "10099", "message": "El apalancamiento supera el maximo permitido." })
        except (errors.OrderError) as exc:
            raise exc
        except (Exception) as exc:
            return exc

        ## Seteo el Apalancamiento
        try:
            if set_leverage(exchange=self.exchange, symbol=self.symbol, leverage=leverage) is False:
                return { "code": "error", "message": "No es posible configurar el apalancamiento. Error: " + str(exc) }
        except (Exception) as exc:
            return exc


        ## Si no hay una orden activa, se crea una orden limit.
        try:
            if create_order(exchange=self.exchange, symbol=self.symbol, order_type=order_type, order_action=order_action, quantity=quantity, entry_price=entry_price, order_id=order_id, time_in_force="PostOnly", stop_loss=stop_loss, reduce_only=False) is False:
            #if(create_order(exchange=self.exchange, symbol=self.symbol, order_type='market', order_action=order_action, quantity=quantity, entry_price=entry_price, order_id=order_id, time_in_force="PostOnly", stop_loss=stop_loss, reduce_only=False, reintentos=2, sleep=1) is False):
                return { "code": "error", "message": "Error al intentar crear la orden." }
        except (Exception) as exc:
            print(exc)
            raise exc

        ## Consultar estado de la orden creada anteriormente. Mediante un bucle por un tiempo de 10s cerrar la orden limit y continuar con el completado por la orden.
        try:
            #limit_order = get_order(exchange=exchange, symbol=SYMBOL, symbol_slash=SYMBOL_SLASH, order_id=order_id, reintentos=40, sleep=1)
            #limit_order = get_order_with_queue(exchange=self.exchange, symbol=self.symbol, order_id=order_id, q_order=self.q_order, reintentos=40, sleep=1)
            time.sleep(1)
            limit_order = get_order_with_queue(exchange=self.exchange, symbol=self.symbol, order_id=order_id, wst=self.wst)
            print("limit_order: ", limit_order )

            reintentos_aux = 90
            while(reintentos_aux > 0 and limit_order is not None and limit_order['order_status'] in ["Created" , "New", "PartiallyFilled"]):
                limit_order = get_order_with_queue(exchange=self.exchange, symbol=self.symbol, order_id=order_id, wst=self.wst)
                reintentos_aux -= 1
                time.sleep(1)


            while check_order_with_queue(exchange=self.exchange, symbol=self.symbol, wst=self.wst) is True:
                cancelar_ordenes(exchange=self.exchange, symbol=self.symbol)
                time.sleep(1.5)

        except (errors.OrderError) as exc:
            raise exc
        except (Exception) as exc:
            exc2 = json.loads(str(exc).replace("bybit ",""))
            if exc2['ret_code'] == 130010:
                pass
            else:
                return exc


        #### Consulto si existe la posicion abierta para el simbolo. ####
        try:
            time.sleep(1.5)
            if check_position_with_queue(exchange=self.exchange, symbol=self.symbol, wst=self.wst) is False:
                logger_strategy.info("La orden no se completo. No existe posicion abierta.")
                raise errors.OrderError({ "code": "10001", "message": "La orden no se completo. No existe posicion abierta." })
        except (errors.OrderError) as exc:
            raise exc
        except (Exception) as exc:
            return exc


        ## Calcular SL y TP utilizando el precio de compra y cantidad completada.

        #### Recalculo stop_loss y TakePofit
        open_pos_detail = get_position_with_queue(exchange=self.exchange, symbol=self.symbol, wst=self.wst)
        logger_position.info('-------------------------------------------------------------------------------')
        logger_position.info("Posicion " + position_side + " abierta. OrderID: " + str(order_id) + " - " + str(open_pos_detail))

        # if(position_side == 'long'):
        #     sl_ret = entry_price_position - (atr * sl_atr)
        #     stop_loss_new = float("{:0.0{}f}".format(float(min(sl_ret, low_price_prev_bar - (atr * 0.2))), self.info_symbol['pricePrecision']))
        #     take_profit = entry_price_position + (abs(entry_price_position - stop_loss_new) * reward_ratio)
        #     take_profit = float("{:0.0{}f}".format(float(take_profit), self.info_symbol['pricePrecision']))
        # else:
        #     sl_ret = entry_price_position + (atr * sl_atr)
        #     stop_loss_new = float("{:0.0{}f}".format(float(min(sl_ret, high_price_prev_bar + (atr * 0.2))), self.info_symbol['pricePrecision']))
        #     take_profit = entry_price_position - (abs(entry_price_position - stop_loss_new) * reward_ratio)
        #     take_profit = float("{:0.0{}f}".format(float(take_profit), self.info_symbol['pricePrecision']))

        quantity_pos = float(open_pos_detail['size'])


        ##Creo orden TP
        try:
            if create_order(exchange=self.exchange, symbol=self.symbol, order_type=order_tp_type, order_action=side_sl_tp, quantity=quantity_pos, entry_price=take_profit, order_id=order_id_tp, time_in_force="PostOnly", reduce_only=True, close_on_trigger=False) is False:
                #return { "code": "error", "message": "Error al intentar crear la orden TP. Error: " + str(e) }
                pass
        except (Exception) as exc:
            return exc

        time.sleep(2)
        try:
            #limit_tp_order = get_order(exchange=exchange, symbol=SYMBOL, symbol_slash=SYMBOL_SLASH, order_id=order_id_tp, reintentos=2, sleep=1)
            limit_tp_order = get_order_with_queue(exchange=self.exchange, symbol=self.symbol, order_id=order_id_tp, wst=self.wst)
            #if(limit_tp_order is None or (limit_tp_order is not None and (limit_tp_order['status'] == "canceled" or limit_tp_order['status'] == "expired"))):
            if(limit_tp_order is None or (limit_tp_order is not None and (limit_tp_order['order_status'] in ["Cancelled", "Rejected"]))):
                logger_strategy.info("Orden TP cancelada o expirada.")
                cerrar_posiciones(exchange=self.exchange, symbol=self.symbol, order_action=side_sl_tp, quantity=quantity_pos, order_id=order_id, wst=self.wst)
                logger_position.info("Posicion cerrada")
                logger_position.info('-------------------------------------------------------------------------------')
                return { "code": "error", "message": "La orden TP no se completo. Estado cancelado o expirado." }
            elif(limit_tp_order is not None and (limit_tp_order['order_status'] == "New")):
                logger_strategy.info("La TP orden se creo correctamente.")
            else:
                logger_strategy.info("La orden TP no existe.")
                return { "code": "error", "message": "La orden TP no existe." }
        except (Exception) as exc:
            return exc


        ## Valido el estado de la posicion
        try:
            while(check_position_with_queue(exchange=self.exchange, symbol=self.symbol, wst=self.wst) is True and check_order_with_queue(exchange=self.exchange, symbol=self.symbol, wst=self.wst) is True):
                #Valido si el precio supera el TP
                ticker = get_ticker_with_queue(exchange=self.exchange, symbol=self.symbol, wst=self.wst)
                last_price = float("{:0.0{}f}".format(float(int(ticker['last_price_e4']) * 0.0001), self.info_symbol['pricePrecision']))
                # last_price = float(ticker['last_price'])
                if((position_side == 'long' and last_price > take_profit and abs((last_price - take_profit)*100/take_profit) > 0.075) or (position_side == 'short' and last_price < take_profit and abs((last_price - take_profit)*100/take_profit) > 0.075)):
                    logger_position.info("El precio supero el TP. Cerrando posicion...")
                    cerrar_posiciones(exchange=self.exchange, symbol=self.symbol, order_action=side_sl_tp, quantity=quantity_pos, order_id=order_id, wst=self.wst)
                    break
                time.sleep(1.5)

            ## Se cierran las ordenes activas por seguridad
            cancelar_ordenes(exchange=self.exchange, symbol=self.symbol)

            # Se cierran las posiciones por seguridad
            cerrar_posiciones(exchange=self.exchange, symbol=self.symbol, order_action=side_sl_tp, quantity=quantity_pos, order_id=order_id, wst=self.wst)

            time.sleep(1)
            if((position_side == 'long' and last_price >= entry_price) or (position_side == 'short' and last_price <= entry_price)):
                logger_position.info("Posicion ganadora")
            else:
                logger_position.info("Posicion perdedora")
            logger_position.info('-------------------------------------------------------------------------------')

            # cancelar_ordenes(exchange=self.exchange, symbol=self.symbol, reintentos=2, sleep=1)
            # cancelar_ordenes_condicionales(exchange=self.exchange, symbol=self.symbol, reintentos=2, sleep=1)
            if(check_position(exchange=self.exchange, symbol=self.symbol) is False and check_orders(exchange=self.exchange, symbol=self.symbol) is False):
                return { "code": "error", "message": "La pocision ya fue cerrada." }
            else:
                return { "code": "error", "message": "Existen ordenes o posiciones activas." }
        except (Exception) as exc:
            return exc


    ##Cancelacion de ordenes SL y TP. Llamada a funcion de cancelacion de todas las ordenes.
        #cancelar_todas_ordenes(exchange, SYMBOL, SYMBOL_SLASH)
        #cancelar_ordenes(exchange=self.exchange, symbol=self.symbol, reintentos=2, sleep=1)
        #cancelar_todas_ordenes_condicionales(exchange, SYMBOL, SYMBOL_SLASH)
        #cancelar_ordenes_condicionales(exchange=self.exchange, symbol=self.symbol, reintentos=2, sleep=1)

        return { "code": "ok", "message": "Fin de la operacion." }
