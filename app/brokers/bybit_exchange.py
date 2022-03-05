import os
import json
import requests
from datetime import datetime
import time
from config import bybit_config
import logging
from utils import log, errors
from pybit import HTTP
from pybit.exceptions import FailedRequestError, InvalidRequestError
import asyncio
import hmac
import hashlib

#import os
#from config.definitions import ROOT_DIR
#print("\n")
#print(os.path.join(ROOT_DIR, 'data', 'mydata.json'))

import os
import sys
sys.path.append("/home/poxy/Projects/tradingbot/app") 

logger_strategy = log.setup_custom_logger('strategy', filename='log/bybit_strategy.log', console=True, log_level=logging.DEBUG)

def get_exchange():
    return HTTP(
        endpoint=bybit_config.REST,
        api_key=bybit_config.API_KEY,
        api_secret=bybit_config.API_SECRET,
        recv_window=bybit_config.RECVWINDOW,
        logging_level=logging.DEBUG,
        force_retry=True,
        retry_delay=3,
        retry_codes={10002, 10006}
        #ignore_codes={20001, 30034}
        )


def obtener_info_symbol(exchange=None, symbol=None):
    logger_strategy.debug("Inicio funcion obtener_info_symbol...")

    info = None
    symbol_info = exchange.query_symbol()
    logger_strategy.debug("Informacion de simbolos: " + str(symbol_info))

    for f in symbol_info['result']:
        if f['name'] == symbol:
            info = { "symbol" : symbol, "pricePrecision": int(f['price_scale']), "quantityPrecision": int(len(str(f['lot_size_filter']['qty_step']).split(".")[1])) }
            logger_strategy.debug("Informacion del simbolo: " + str(info))
            json_object = json.dumps(info, indent = 4)
            with open("data/conf_bybit_bot.json", "w") as outfile:
                outfile.write(json_object)
            break

    logger_strategy.debug("Fin funcion obtener_info_symbol...")
    return info


#### Generar funcion de validacion de Margin al iniciar el Bot en main.py
def cambiar_margin_type_symbol(exchange=None, symbol=None):
    logger_strategy.debug("Inicio funcion cambiar_margin_type_symbol...")

    response = False
    try:
        margin = exchange.cross_isolated_margin_switch(symbol=symbol, is_isolated=True, buy_leverage=1, sell_leverage=1)
        logger_strategy.debug("margin: " + str(margin))
        if(margin['ret_msg'] == 'OK' and margin['ret_code'] == 0):
            logger_strategy.info("Margin type modificado a ISOLATED")
            response = True
    except (InvalidRequestError) as exc:
        if '130056' in str(exc):
            logger_strategy.info("No es necesario modificar el Margin Type.")
            response = True
        elif '130129' in str(exc):
            logger_strategy.info("No es necesario modificar el Margin Type.")
            response = True
        else:
            logger_strategy.error("Error cambio de margin type" + str(exc))
            response = False
    except (Exception, requests.exceptions.ReadTimeout) as exc:
        logger_strategy.error("Error cambio de margin type" + str(exc))
        response = False

    logger_strategy.debug("Margin response: " + str(response))
    logger_strategy.debug("Fin funcion cambiar_margin_type_symbol...")
    return response


def is_valid_passphrase(exchange_name, request_passphrase):
    logger_strategy.debug("Fin funcion is_valid_passphrase...")

    is_valid = False
    passphrase = eval('{}'.format(exchange_name + "_config.WEBHOOK_PASSPHRASE"))
    logger_strategy.debug("request_passphrase: " + str(request_passphrase))
    logger_strategy.debug("passphrase: " + str(passphrase))
    if request_passphrase == passphrase:
        is_valid = True
    else:
        is_valid = False

    logger_strategy.debug("is_valid_passphrase: " + str(is_valid))
    logger_strategy.debug("Fin funcion is_valid_passphrase...")
    return is_valid


def get_info_symbol(exchange=None, symbol=None, info_symbol=None):
    logger_strategy.debug("Inicio funcion get_info_symbol...")

    info_symbol = None
    try:
        if not os.path.exists('data/conf_bybit_bot.json'):
            logger_strategy.debug("Archivo de configuracion inexistente")
            info_symbol = obtener_info_symbol(exchange=exchange, symbol=symbol)
            # logger_strategy.info("Configuracion precision respuesta: " + str(info_symbol))
        else:
            with open('data/conf_bybit_bot.json', 'r') as openfile:
                info_symbol = json.load(openfile)
                if info_symbol['symbol'] == symbol:
                    logger_strategy.debug("Configuracion recuperada de archivo (conf_bybit_bot.json): " + str(info_symbol))
                else:
                    logger_strategy.debug("La configuracion del symbolo no coincide.")
                    info_symbol = obtener_info_symbol(exchange=exchange, symbol=symbol)
                    logger_strategy.debug("Configuracion precision respuesta: " + str(info_symbol))

        return info_symbol
    except (Exception) as exc:
        logger_strategy.error("La informacion del symbol esta vacia.")

    logger_strategy.debug("Fin funcion get_info_symbol...")
    return info_symbol


def obtener_kline_symbol(exchange=None, symbol=None, timeframe=15, time_from=None, limit=200 ):
    #logger_strategy.debug("Inicio funcion obtener_kline_symbol...")

    kline_info = None
    try:
        #print(int(time_from*1000))
        time_from_new = (time_from) - ((limit * timeframe)*60) + (timeframe * 2)
        #print(int(time_from_new*1000))
        kline_info = exchange.query_kline(symbol=symbol, interval=str(timeframe), **{'from':int(time_from_new)})['result']
    except (Exception, requests.exceptions.ReadTimeout) as exc:
        logger_strategy.error("No es posible consultar el simbolo. Error: " + str(exc))

    #logger_strategy.debug("kline_info: " + str(kline_info))
    #logger_strategy.debug("Fin funcion obtener_kline_symbol...")
    return kline_info


def get_ticker(exchange=None, symbol=None):
    logger_strategy.debug("Inicio funcion get_ticker...")

    ticker = None
    try:
        # ticker = exchange.Market.Market_symbolInfo(symbol=symbol).result()[0]['result'][0]
        ticker = exchange.latest_information_for_symbol(symbol=symbol)['result'][0]
    except (Exception, requests.exceptions.ReadTimeout) as exc:
        logger_strategy.error("No es posible consultar el simbolo. Error: " + str(exc))

    logger_strategy.debug("ticker: " + str(ticker))
    logger_strategy.debug("Fin funcion get_ticker...")
    return ticker


def get_ticker_with_queue(exchange=None, symbol=None, wst=None):
    logger_strategy.debug("Inicio funcion get_ticker_with_queue...")

    ticker = wst.ws_unauth.fetch('instrument_info.100ms.' + str(symbol))
    # if(not q_ticker.empty()):
        # ticker = q_ticker.queue[q_ticker.qsize()-1]

    logger_strategy.debug("ticker_with_queue: " + str(ticker))
    logger_strategy.debug("Fin funcion get_ticker_with_queue...")
    return ticker


def check_position(exchange=None, symbol=None):
    logger_strategy.debug("Inicio funcion check_position...")

    response = False
    try:
        # list_open_positions = exchange.LinearPositions.LinearPositions_myPosition(symbol=symbol).result()[0]['result']
        list_open_positions = exchange.my_position(symbol=symbol)['result']
        logger_strategy.debug("list_open_positions: " + str(list_open_positions))
        if len(list_open_positions) > 0:
            for f in list_open_positions:
                if (f['symbol'] == symbol and float(f['size']) > 0):
                    response = True
                    break
    except (Exception, requests.exceptions.ReadTimeout) as exc:
        logger_strategy.error("No es posible consultar las posiciones. Error: " + str(exc))
        # return { "code": "error", "message": "No es posible consultar las posiciones. Error: " + str(e) }
        response = False

    logger_strategy.debug("response: " + str(response))
    logger_strategy.debug("Fin funcion check_position...")
    return response


def check_position_with_queue(exchange=None, symbol=None, wst=None):
    logger_strategy.debug("Inicio funcion check_position_with_queue...")

    response = False
    position = wst.ws_auth.fetch('position')
    if position:
        position_buy = position[str(symbol)]['Buy']
        position_sell = position[str(symbol)]['Sell']
        if (float(position_buy['size']) > 0.0 or float(position_sell['size']) > 0.0):
            response = True

    logger_strategy.debug("check_position_with_queue: " + str(position))
    logger_strategy.debug("Fin funcion check_position_with_queue...")
    return response


def get_balance(exchange=None, coin='USDT'):
    logger_strategy.debug("Inicio funcion get_balance...")

    balance = 0.0
    try:
        balance = float(exchange.get_wallet_balance(coin="USDT")['result'][coin]['available_balance'])
    except (Exception, requests.exceptions.ReadTimeout) as exc:
        logger_strategy.error("No es posible consultar el balance de la cuenta. Error: " + str(exc))
        return { "code": "error", "message": "No es posible consultar el balance de la cuenta. Error: " + str(exc) }

    logger_strategy.debug("balance: " + str(balance))
    logger_strategy.debug("Fin funcion get_balance...")
    return balance


def get_position(exchange=None, symbol=None):
    logger_strategy.debug("Inicio funcion get_position...")

    try:
        # list_open_positions = exchange.LinearPositions.LinearPositions_myPosition(symbol=symbol).result()[0]['result']
        list_open_positions = exchange.my_position(symbol=symbol)['result']
        logger_strategy.debug("list_open_positions: " + str(list_open_positions))
        open_pos_detail = None
        if list_open_positions:
            for f in list_open_positions:
                if f['symbol'] == symbol and float(f['size']) > 0:
                    logger_strategy.debug("Se encontro una posicion")
                    open_pos_detail = f
                    # logger_strategy.info("open_pos_detail: " + str(f))
                    # return open_pos_detail
                    #telegram_bot_sendtext("open_pos_detail: " + str(f))
                    break
    except (Exception, requests.exceptions.ReadTimeout) as exc:
            logger_strategy.error("No es posible consultar las pocisiones. Error: " + str(exc))
            return { "code": "error", "message": "No es posible consultar las pocisiones. Error: " + str(exc) }

    logger_strategy.debug("open_pos_detail: " + str(f))
    logger_strategy.debug("Fin funcion get_position...")
    return open_pos_detail

def get_position_with_queue(exchange=None, symbol=None, wst=None):
    logger_strategy.debug("Inicio funcion get_position_with_queue...")

    open_pos_detail = None
    position = wst.ws_auth.fetch('position')
    if(position):
        position_buy = position[str(symbol)]['Buy']
        position_sell = position[str(symbol)]['Sell']
        # position = q_position.queue[q_position.qsize()-1]
        if float(position_buy['size']) > 0.0:
            open_pos_detail = position_buy
        else:
            open_pos_detail = position_sell
    else:
        logger_strategy.error("No es posible consultar las pocisiones. Lista vacia.")
    # return None

    logger_strategy.debug("open_pos_detail: " + str(open_pos_detail))
    logger_strategy.debug("Fin funcion get_position_with_queue...")
    return open_pos_detail


def check_orders(exchange=None, symbol=None):
    logger_strategy.debug("Inicio funcion check_orders...")

    list_orders = None
    response = False
    try:
        # list_orders = exchange.LinearOrder.LinearOrder_query(symbol=symbol).result()[0]['result']
        list_orders = exchange.query_active_order(symbol=symbol)['result']
        if list_orders:
            logger_strategy.debug("list_orders: " + str(list_orders))
            for f in list_orders:
                if f['symbol'] == symbol:
                    response = True
                    break
    except (Exception, requests.exceptions.ReadTimeout) as exc:
        logger_strategy.error("No es posible consultar las ordenes. Error: " + str(exc))
        response = False

    logger_strategy.debug("Fin funcion check_orders...")
    return response


def get_order(exchange=None, symbol=None, order_id=None):
    limit_order = None
    try:
        # limit_order = exchange.LinearOrder.LinearOrder_query(symbol=symbol, order_link_id=order_id).result()[0]['result']
        limit_order = exchange.query_active_order(symbol=symbol, order_link_id=order_id)
        # if(limit_order is not None and limit_order['status'] != "open"):
        return limit_order
    except (Exception, requests.exceptions.ReadTimeout) as exc:
        logger_strategy.error("No es posible consultar la ordene. Error: " + str(exc))
        return limit_order


def get_order_with_queue(exchange=None, symbol=None, order_id=None, wst=None):
    logger_strategy.debug("Inicio funcion get_order_with_queue...")

    limit_order = None
    order = wst.ws_auth.fetch('order')
    if order:
        order_tmp = order[len(order)-1]
        # order = q_order.queue[q_order.qsize()-1]
        logger_strategy.debug("order: " + str(order_tmp))
        # if(order is not None and order['order_link_id'] == order_id):
        if(order_tmp['symbol'] == symbol and order_tmp['order_link_id'] == order_id):
            limit_order = order_tmp

    logger_strategy.debug("limit_order: " + str(limit_order))
    logger_strategy.debug("Fin funcion get_order_with_queue...")
    return limit_order


def check_order_with_queue(exchange=None, symbol=None, wst=None):
    logger_strategy.debug("Inicio funcion check_order_with_queue...")

    response = False
    limit_order = wst.ws_auth.fetch('order')
    if limit_order:
        limit_order_tmp = limit_order[len(limit_order)-1]
        # limit_order = q_order.queue[q_order.qsize()-1]
        logger_strategy.debug("limit_order: " + str(limit_order_tmp))
        # if (limit_order is not None and limit_order['order_status'] in ["Created" , "New", "PartiallyFilled"]):
        if(limit_order_tmp['symbol'] == symbol and limit_order_tmp['order_status'] in ["Created" , "New", "PartiallyFilled"]):
            response = True

    logger_strategy.debug("response: " + str(response))
    logger_strategy.debug("Fin funcion check_order_with_queue...")
    return response

def set_leverage(exchange=None, symbol=None, leverage=1):
    logger_strategy.debug("Inicio funcion set_leverage...")

    response = False
    try:
        # order_leverage = exchange.LinearPositions.LinearPositions_saveLeverage(symbol=symbol, buy_leverage=leverage, sell_leverage=leverage).result()[0]
        order_leverage = exchange.set_leverage(symbol=symbol, buy_leverage=leverage, sell_leverage=leverage)
        logger_strategy.debug("order_leverage: " + str(order_leverage))
        if(order_leverage['ret_msg'] == 'OK' and order_leverage['ret_code'] == 0):
            logger_strategy.info("Configuracion de apalancamiento: " + str(order_leverage))
            response = True
    except (InvalidRequestError) as exc:
        if '34036' in str(exc):
            logger_strategy.info("No es necesario modificar el apalancamiento.")
            response = True
        else:
            logger_strategy.error("No es posible configurar el apalancamiento." + str(exc))
            response = False
    except (Exception, requests.exceptions.ReadTimeout) as exc:
        # e2 = json.loads(str(e).replace("bybit ",""))
        # if(e2['ret_code'] == 34036):
        #     logger_strategy.info("No es necesario modificar el Leverage.")
        #     return True
            #break
        logger_strategy.error("No es posible configurar el apalancamiento. Error: " + str(exc))
        response = False
            #return { "code": "error", "message": "No es posible configurar el apalancamiento. Error: " + str(e) }

    logger_strategy.debug("response: " + str(response))
    logger_strategy.debug("Fin funcion set_leverage...")
    return response


def create_order(exchange=None, symbol=None, order_type=None, order_action=None, quantity=None, entry_price=None, order_id=None, time_in_force=None, stop_loss=None, reduce_only=None, close_on_trigger=False):
    logger_strategy.debug("Inicio funcion create_order...")

    response = False
    try:
        if stop_loss is None:
            logger_strategy.debug("Inicio creacion orden TP")
            # order_tp_response = exchange.LinearOrder.LinearOrder_new(side=order_action.capitalize(), symbol=symbol, order_type=order_type.capitalize(), qty=quantity, price=entry_price, order_link_id=order_id, time_in_force=time_in_force, reduce_only=reduce_only, close_on_trigger=close_on_trigger).result()[0]
            order_tp_response = exchange.place_active_order(side=order_action.capitalize(), symbol=symbol, order_type=order_type.capitalize(), qty=quantity, price=entry_price, order_link_id=order_id, time_in_force=time_in_force, reduce_only=reduce_only, close_on_trigger=close_on_trigger)
            logger_strategy.debug("order_tp_response: " + str(order_tp_response))
            if(order_tp_response['ret_msg'] == 'OK' and order_tp_response['ret_code'] == 0):
                logger_strategy.info("Orden TP creada: " + str(order_tp_response))
                response = True
        else:
            logger_strategy.debug("Inicio creacion orden")
            # order_response = exchange.LinearOrder.LinearOrder_new(side=order_action.capitalize(), symbol=symbol, order_type=order_type.capitalize(), qty=quantity, price=entry_price, order_link_id=order_id, time_in_force=time_in_force, stop_loss=stop_loss, reduce_only=reduce_only, close_on_trigger=close_on_trigger).result()[0]
            order_response = exchange.place_active_order(side=order_action.capitalize(), symbol=symbol, order_type=order_type.capitalize(), qty=quantity, price=entry_price, order_link_id=order_id, time_in_force=time_in_force, stop_loss=stop_loss, reduce_only=reduce_only, close_on_trigger=close_on_trigger)
            logger_strategy.debug("order_response: " + str(order_response))
            if(order_response['ret_msg'] == 'OK' and order_response['ret_code'] == 0):
                logger_strategy.info("Orden creada: " + str(order_response))
                response = True
    except (Exception, requests.exceptions.ReadTimeout) as exc:
        logger_strategy.error("Error al intentar crear la orden. Error: " + str(exc))
        response = False

    logger_strategy.debug("response: " + str(response))
    logger_strategy.debug("Fin funcion create_order...")
    return response


def cancelar_ordenes(exchange=None, symbol=None):
    logger_strategy.debug("Inicio funcion cancelar_ordenes...")

    open_orders = True
    try:
        # cancel_all_orders = exchange.LinearOrder.LinearOrder_cancelAll(symbol=symbol).result()[0]
        cancel_all_orders = exchange.cancel_all_active_orders(symbol=symbol)
        logger_strategy.debug("cancel_all_orders: " + str(cancel_all_orders))
    except (Exception, requests.exceptions.ReadTimeout) as exc:
            logger_strategy.error("No es posible cancelar ordenes activas. Error: " + str(exc))

    flag_open_orders = 1
    time.sleep(1.5)

    open_orders = check_orders(exchange=exchange, symbol=symbol)
    logger_strategy.debug("open_orders: " + str(open_orders))
    if(open_orders is False):
        flag_open_orders = 0
        logger_strategy.info("No existen ordenes abiertas de TP y SL.")


    logger_strategy.debug("flag_open_orders: " + str(flag_open_orders))
    while flag_open_orders == 1:
        try:
            # cancel_all_orders = exchange.LinearOrder.LinearOrder_cancelAll(symbol=symbol).result()[0]
            cancel_all_orders = exchange.cancel_all_active_orders(symbol=symbol)
            logger_strategy.debug("cancel_all_orders: " + str(cancel_all_orders))
        except (Exception, requests.exceptions.ReadTimeout) as exc:
            logger_strategy.error("No es posible cancelar ordenes activas. Error: " + str(exc))

        open_orders = True
        try:
            open_orders = check_orders(exchange=exchange, symbol=symbol)
            logger_strategy.debug("open_orders: " + str(open_orders))
            if open_orders is False:
                flag_open_orders = 0
                logger_strategy.info("No existen ordenes abiertas de TP y SL.")
                break
        except (Exception, requests.exceptions.ReadTimeout) as exc:
            logger_strategy.error("No es posible cancelar ordenes activas. Error: " + str(exc))

    logger_strategy.debug("Fin funcion cancelar_ordenes...")


def cerrar_posiciones(exchange=None, symbol=None, order_action=None, quantity=None, order_id=None, wst=None):
    logger_strategy.debug("Inicio funcion cerrar_posiciones...")

    is_position = True
    try:
        is_position = check_position_with_queue(exchange=exchange, symbol=symbol, wst=wst)
        logger_strategy.debug("is_position: " + str(is_position))
        if is_position is True:
            # order_close_position = create_order(exchange=exchange, symbol=symbol, symbol_slash=symbol_slash, order_type='market', order_action=order_action, quantity=quantity, order_id=str(order_id)+'c', reduce_only=False, close_on_trigger=True, reintentos=2, sleep=1)
            # order_close_position = exchange.LinearOrder.LinearOrder_new(side=order_action.capitalize(), symbol=symbol, order_type='Market', qty=quantity, order_link_id=str(order_id)+'c', time_in_force='GoodTillCancel', reduce_only=False, close_on_trigger=True).result()[0]
            order_close_position = exchange.place_active_order(side=order_action.capitalize(), symbol=symbol, order_type='Market', qty=quantity, order_link_id=str(order_id)+'c', time_in_force='GoodTillCancel', reduce_only=False, close_on_trigger=True)
            logger_strategy.debug("order_close_position: " + str(order_close_position))
            if(order_close_position['ret_msg'] == 'OK' and order_close_position['ret_code'] == 0):
                logger_strategy.info("Orden de cierre de posiciones: " + str(order_close_position))
    except (Exception, requests.exceptions.ReadTimeout) as exc:
        logger_strategy.error("Reintentando... " + str(exc))

    is_position = True
    try:
        #while(check_position(exchange=exchange, symbol=symbol, symbol_slash=symbol_slash, reintentos=3, sleep=1) == True):
        is_position = check_position_with_queue(exchange=exchange, symbol=symbol, wst=wst)
        logger_strategy.debug("is_position: " + str(is_position))
        while is_position is True:
            #print("Sigo en posicion.")
            time.sleep(1)
        #open_pos_detail = get_position(exchange=exchange, symbol=symbol, symbol_slash=symbol_slash, reintentos=2, sleep=1)
        open_pos_detail = get_position_with_queue(exchange=exchange, symbol=symbol, wst=wst)
        logger_strategy.debug("open_pos_detail: " + str(open_pos_detail))
        if open_pos_detail is None or not open_pos_detail:
            logger_strategy.info("La posicion fue cerrada a Market.")
            return { "code": "info", "message": "La posicion fue cerrada a Market." }
    except (Exception) as exc:
        return exc

    logger_strategy.debug("Fin funcion cerrar_posiciones...")
