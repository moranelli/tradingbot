import asyncio
import json
import logging
import threading
import queue
from web.mythread import MyThread
import time
from utils import log, errors
# import requests

import nest_asyncio
from backtests.hawk_strategy import Strategy
from backtests.bot_indicator import BotIndicator
from brokers.bybit_exchange import obtener_info_symbol, cambiar_margin_type_symbol, get_exchange, is_valid_passphrase, check_orders, check_position, get_info_symbol
from bybit_websocket import BybitWebsocket
from config import bybit_config
from fastapi import BackgroundTasks, FastAPI, Request, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime
from fastapi.responses import JSONResponse
# from pyinstrument import Profiler

nest_asyncio.apply()

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

IN_STRATEGY = False
IN_POSITION = False

EXCHANGE = None


## Configuracion de logging
logger_strategy = log.setup_custom_logger('strategy', filename='log/bybit_strategy.log', console=True, log_level=logging.DEBUG)

# app = FastAPI()
app = FastAPI(title='CustomLogger', debug=True)

app.mount("/static", StaticFiles(directory="web/static"), name="static")

templates = Jinja2Templates(directory="web/templates")

#### Pre-Configuracion Bot ####
EXCHANGE = get_exchange()


# Whitelisted IPs
WHITELISTED_IPS = ["portalpox.duckdns.org", "127.0.0.1", "172.18.0.1", "191.83.166.185", "191.83.167.111"]

@app.middleware('http')
async def validate_ip(request: Request, call_next):
    # Get client IP
    ip = str(request.client.host)

    # Check if IP is allowed
    if ip not in WHITELISTED_IPS:
        data = {
            'message': f'IP {ip} is not allowed to access this resource.'
        }
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=data)

    # Proceed if IP is allowed
    return await call_next(request)


#@app.get("/", response_class=HTMLResponse)
#async def index(request: Request):
#    #logger_strategy.info(request)
#    return templates.TemplateResponse("index.html", {"request": request})


@app.post('/conf')
async def conf(request: Request):
    global EXCHANGE

    conf = await request.json()
    logger_strategy.info("Configuracion de precision recibida: " + str(conf))
    ## Validacion de Passphrase
    if is_valid_passphrase(exchange_name=EXCHANGE_NAME, request_passphrase=conf['passphrase']) is False:
        logger_strategy.error("Frase de contraseña invalida")
        return { "code": "error", "message": "Frase de contraseña invalida" }
    else:
        global INFO_SYMBOL
        INFO_SYMBOL = obtener_info_symbol(exchange=EXCHANGE, symbol=conf['symbol'])
        logger_strategy.info("Configuracion precision respuesta: " + str(INFO_SYMBOL))
        return INFO_SYMBOL


@app.post('/webhook')
async def webhook(request: Request):
    logger_strategy.debug("Inicio funcion webhook...")

    global EXCHANGE
    global SYMBOL
    global TIMEFRAME
    global INFO_SYMBOL
    global WST

    data = await request.json()
    logger_strategy.info("Request: " + str(data))

    ## Validacion de Passphrase
    if data['passphrase'] == "yourpassphrasepoxystatus":
        logger_strategy.info("Frase de contraseña de status")
        return { "code": "info", "message": "Frase de contraseña de status" }

    if is_valid_passphrase(exchange_name=EXCHANGE_NAME, request_passphrase=data['passphrase']) is False:
        logger_strategy.error("Frase de contraseña invalida")
        return { "code": "error", "message": "Frase de contraseña invalida" }


    start_strategy(data)

    logger_strategy.debug("Fin funcion webhook...")
    return "Fin Estrategia"


def start_strategy(data):
    logger_strategy.debug("Inicio funcion webhook...")

    global EXCHANGE
    global SYMBOL
    global TIMEFRAME
    global INFO_SYMBOL
    global WST
    global IN_STRATEGY
    global IN_POSITION

    request_symbol = data['ticker'].replace("PERP", "")
    logger_strategy.info('-------------------------------------------------------------------------------')
    logger_strategy.info("Request: " + str(data))

    ## Validacion de IN_STRATEGY
    if IN_STRATEGY:
        logger_strategy.error("Solo se permite una operacion a la vez. Estrategia en curso.")
        return { "code": "error", "message": "Solo se permite una operacion a la vez. Estrategia en curso." }


    ## Validacion de SYMBOL
    if SYMBOL != request_symbol:
        logger_strategy.error("El simbolo del alerta no coincide con la configuracion del BOT")
        return { "code": "error", "message": "El simbolo del alerta no coincide con la configuracion del BOT" }

    ## Validacion de Websockets
    while WST is None:
        start_websockets()

    ## Validacion de Exchange
    while EXCHANGE is None:
        EXCHANGE = get_exchange()

    ## Validacion de posicion u ordenes en curso
    if check_orders(exchange=EXCHANGE, symbol=SYMBOL) is True or check_position(exchange=EXCHANGE, symbol=SYMBOL) is True:
        logger_strategy.warning("Solo se permite una operacion a la vez.")
        logger_strategy.info('-------------------------------------------------------------------------------')
        IN_POSITION = True
        return { "code": "error", "message": "Solo se permite una operacion a la vez." }


    ## Seteo inicial de MarginType y modo de tp_sl
    cambiar_margin_type_symbol(exchange=EXCHANGE, symbol=SYMBOL)

    if INFO_SYMBOL == "":
        INFO_SYMBOL = get_info_symbol()(exchange=EXCHANGE, symbol=SYMBOL, info_symbol=INFO_SYMBOL)

    #Inicio de Profiler
    #profiler = Profiler()
    #profiler.start()

    logger_strategy.info('*** Inicio de la estrategia ***')

    q_order.queue.clear()
    q_position.queue.clear()
    strategy = Strategy(exchange=EXCHANGE, data=data, symbol=SYMBOL, timeframe=TIMEFRAME, info_symbol=INFO_SYMBOL, wst=WST)
    thread_strategy = MyThread(target=strategy.strategy, args=(0,))

    try:
        IN_STRATEGY = True
        thread_strategy.start()
        thread_strategy.join()
    except (errors.OrderError) as exc:
        logger_strategy.info("Reintentando Estrategia por orden cancelada.")
        try:
            thread_strategy = MyThread(target=strategy.strategy, args=(1,))
            IN_STRATEGY = True
            thread_strategy.start()
            thread_strategy.join()
        except (errors.OrderError) as exc:
            return str(exc)
    finally:
        # q_ticker.queue.clear()
        q_order.queue.clear()
        q_position.queue.clear()
        IN_STRATEGY = False
        IN_POSITION = False
        logger_strategy.info('*** Fin de la estrategia ***')
        logger_strategy.info('-------------------------------------------------------------------------------')



@app.post('/start_websocket')
async def start_websocket(request: Request, background_tasks: BackgroundTasks):
    logger_strategy.debug("Inicio funcion start_websocket...")

    global EXCHANGE
    global INFO_SYMBOL
    global WST

    data = await request.json()

    ## Validacion de passphrase
    if is_valid_passphrase(exchange_name=EXCHANGE_NAME, request_passphrase=data['passphrase']) is False:
        logger_strategy.error("Frase de contraseña invalida")
        return { "code": "error", "message": "Frase de contraseña invalida" }

    # create console handler and set level to debug
    logger_strategy.info("Iniciando websockets...")
    start_websockets()

    logger_strategy.info("Websockets iniciados")
    logger_strategy.debug("Fin funcion start_websocket...")
    return { "code": "info", "message": "Websockets iniciados" }


@app.post('/stop_websocket')
async def stop_websocket(request: Request):

    global WST
    global q_ticker
    global q_order
    global q_position

    data = await request.json()

    ## Validacion de passphrase
    if is_valid_passphrase(exchange_name=EXCHANGE_NAME, request_passphrase=data['passphrase']) is False:
        logger_strategy.error("Frase de contraseña invalida")
        return { "code": "error", "message": "Frase de contraseña invalida" }

    logger_strategy.info("Finalizando websockets...")

    if WST is not None:
        logger_strategy.info("Finalizando WST")
        WST.ws_unauth.exit()
        WST.ws_auth.exit()
        while(WST.ws_unauth.exited is False or WST.ws_auth.exited is False):
            time.sleep(1)
        WST.ws_unauth = None
        WST.ws_auth = None
        WST = None
        q_ticker.queue.clear()
        q_order.queue.clear()
        q_position.queue.clear()
        logger_strategy.info('WST finalizado')
    else:
        logger_strategy.info("WST no esta iniciado")

    logger_strategy.info('Websockets detenidos')

    return { "code": "info", "message": "Websockets detenidos" }


@app.post('/get_ticker')
async def get_ticker(request: Request):

    global SYMBOL
    global WST

    print(await request.body())

    data = await request.json()

    ## Validacion de passphrase
    if is_valid_passphrase(exchange_name=EXCHANGE_NAME, request_passphrase=data['passphrase']) is False:
        logger_strategy.error("Frase de contraseña invalida")
        return { "code": "error", "message": "Frase de contraseña invalida" }


    if WST is not None:
        logger_strategy.info("ticker")
        if WST.ws_unauth.exited is False:
            response = WST.ws_unauth.fetch('instrument_info.100ms.' + str(SYMBOL))
        else:
            response = None

    return response


@app.post('/get_order')
async def get_order(request: Request):

    global SYMBOL
    global WST

    data = await request.json()

    ## Validacion de passphrase
    if is_valid_passphrase(exchange_name=EXCHANGE_NAME, request_passphrase=data['passphrase']) is False:
        logger_strategy.error("Frase de contraseña invalida")
        return { "code": "error", "message": "Frase de contraseña invalida" }

    if WST is not None:
        logger_strategy.info("order")
        if WST.ws_auth.exited is False:
            response = WST.ws_auth.fetch('order')
        else:
            response = None

    return response


@app.post('/get_position')
async def get_position(request: Request):

    global SYMBOL
    global WST

    data = await request.json()

    ## Validacion de passphrase
    if is_valid_passphrase(exchange_name=EXCHANGE_NAME, request_passphrase=data['passphrase']) is False:
        logger_strategy.error("Frase de contraseña invalida")
        return { "code": "error", "message": "Frase de contraseña invalida" }

    if WST is not None:
        logger_strategy.info("position")
        if WST.ws_auth.exited is False:
            response = WST.ws_auth.fetch('position')
        else:
            response = None

    return response


@app.post('/get_kline')
async def get_kline(request: Request):

    global SYMBOL
    global TIMEFRAME
    global WST

    data = await request.json()

    ## Validacion de passphrase
    if is_valid_passphrase(exchange_name=EXCHANGE_NAME, request_passphrase=data['passphrase']) is False:
        logger_strategy.error("Frase de contraseña invalida")
        return { "code": "error", "message": "Frase de contraseña invalida" }

    if WST is not None:
        logger_strategy.info("kline")
        if WST.ws_unauth.exited is False:
            response = WST.ws_unauth.fetch('candle.' + str(TIMEFRAME) + '.' + str(SYMBOL))
        else:
            response = None

    return response


def is_connected_websockets():
    logger_strategy.debug("Inicio funcion is_connected_websockets...")
    global WST

    response = False

    logger_strategy.debug("is_connected_websockets: " + str(response))
    logger_strategy.debug("Fin funcion is_connected_websockets...")
    return response


def start_websockets():
    logger_strategy.debug("Inicio funcion start_websockets...")

    global EXCHANGE
    global SYMBOL
    global INFO_SYMBOL
    global WST
    global q_ticker
    global q_order
    global q_position
    global TIMEFRAME

    if INFO_SYMBOL == "":
        INFO_SYMBOL = get_info_symbol(exchange=EXCHANGE, symbol=SYMBOL, info_symbol=INFO_SYMBOL)

    ## Validacion de Websockets
    # if(WST_ticker is None or not WST_ticker.is_WST_connected):
    logger_strategy.info("Iniciando websocket...")
    q_ticker.queue.clear()
    q_order.queue.clear()
    q_position.queue.clear()
    WST = BybitWebsocket(symbol=SYMBOL, q_ticker=q_ticker, q_order=q_order, q_position=q_position, timeframe=TIMEFRAME)
    WST.connect()
    logger_strategy.info("websocket iniciado")
    # else:
    #     logger_strategy.info("WST_ticker ya esta iniciado")
    #if(WST_ticker is None or not WST_ticker.is_WST_connected):
    #     logger_strategy.info("Iniciando WST_ticker...")
    #     q_ticker.queue.clear()
    #     WST_ticker = BybitWebsocket(exchange=exchange, symbol=SYMBOL, INFO_SYMBOL=INFO_SYMBOL, WST_queue=q_ticker, load_queue=start_load_queue_event)
    #     WST_ticker.connect(endpoint=bybit_config.WS_PUBLIC, send_command="subscribe", subscription=["instrument_info.100ms." + str(SYMBOL)], shouldAuth=False)
    #     logger_strategy.info("WST_ticker iniciado")
    # else:
    #     logger_strategy.info("WST_ticker ya esta iniciado")

    # if(WST_order is None or not WST_order.is_WST_connected):
    #     logger_strategy.info("Iniciando WST_order...")
    #     q_order.queue.clear()
    #     WST_order = BybitWebsocket(exchange=exchange, symbol=SYMBOL, INFO_SYMBOL=INFO_SYMBOL, WST_queue=q_order, load_queue=start_load_queue_event)
    #     WST_order.connect(endpoint=bybit_config.WS_PRIVATE, send_command="subscribe", subscription=["order"], shouldAuth=True)
    #     logger_strategy.info("WST_order iniciado")
    # else:
    #     logger_strategy.info("WST_order ya esta iniciado")

    # if(WST_position is None or not WST_position.is_WST_connected):
    #     logger_strategy.info("Iniciando WST_position...")
    #     q_position.queue.clear()
    #     WST_position = BybitWebsocket(exchange=exchange, symbol=SYMBOL, INFO_SYMBOL=INFO_SYMBOL, WST_queue=q_position, load_queue=start_load_queue_event)
    #     WST_position.connect(endpoint=bybit_config.WS_PRIVATE, send_command="subscribe", subscription=["position"], shouldAuth=True)
    #     logger_strategy.info("WST_position iniciado")
    # else:
    #     logger_strategy.info("WST_position ya esta iniciado")

    #return WST

    logger_strategy.debug("Fin funcion start_websockets...")


@app.post('/start_bot_indicator')
async def start_bot_indicator(request: Request):
    logger_strategy.debug("Inicio start_bot_indicator...")

    global EXCHANGE
    global SYMBOL
    global TIMEFRAME
    global INFO_SYMBOL
    global WST
    global botIndicator
    global bot_indicator_event

    data = await request.json()

    ## Validacion de Passphrase
    if is_valid_passphrase(exchange_name=EXCHANGE_NAME, request_passphrase=data['passphrase']) is False:
        logger_strategy.error("Frase de contraseña invalida")
        return { "code": "error", "message": "Frase de contraseña invalida" }

    ## Validacion de Websockets
    while WST is None:
        start_websockets()

    ## Validacion de Exchange
    while EXCHANGE is None:
        EXCHANGE = get_exchange()

    if INFO_SYMBOL == "":
        INFO_SYMBOL = get_info_symbol(exchange=EXCHANGE, symbol=SYMBOL, info_symbol=INFO_SYMBOL)

    if not botIndicator is None:
        logger_strategy.error("El bot_indicator esta iniciado")
        return { "code": "error", "message": "El bot_indicator esta iniciado" }

    logger_strategy.info('*** Inicio de botIndicator ***')

    botIndicator = BotIndicator(exchange=EXCHANGE, data=data, symbol=SYMBOL, timeframe=TIMEFRAME, info_symbol=INFO_SYMBOL, wst=WST, bot_indicator_event=bot_indicator_event)
    thread_bot_indicator = MyThread(target=botIndicator.botIndicator)

    try:
        bot_indicator_event.clear()
        thread_bot_indicator.start()
    except (errors.OrderError) as exc:
        logger_strategy.info("Error al iniciar botIndicator: " + str(exc))
    finally:
        logger_strategy.info('*** Fin de botIndicator ***')
        logger_strategy.info('-------------------------------------------------------------------------------')

    logger_strategy.debug("Fin start_bot_indicator...")
    return "Fin start_bot_indicator"


@app.post('/stop_bot_indicator')
async def stop_bot_indicator(request: Request):

    global botIndicator
    global bot_indicator_event

    data = await request.json()

    ## Validacion de passphrase
    if is_valid_passphrase(exchange_name=EXCHANGE_NAME, request_passphrase=data['passphrase']) is False:
        logger_strategy.error("Frase de contraseña invalida")
        return { "code": "error", "message": "Frase de contraseña invalida" }

    logger_strategy.info("Finalizando bot_indicator...")

    bot_indicator_event.set()
    time.sleep(5)
    botIndicator = None

    logger_strategy.info('bot_indicator detenido')

    return { "code": "info", "message": "bot_indicator detenido" }
