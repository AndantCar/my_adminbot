#!/usr/bin/python3
# -*- encoding:utf-8 -*-


import json
import logging

import zmq
import telebot

from osomatli import binance
from tools_telegram import tools, texts_out


level_log = '2'
levels = {'1': logging.DEBUG,
          '2': logging.INFO,
          '3': logging.WARNING,
          '4': logging.ERROR,
          '5': logging.CRITICAL}

logger = logging.getLogger('BinanceBot')

__author__ = 'Carlos Añorve'
__version__ = '1.0'
__all__ = []

logger.info('inicializando todo lo necesario...')

TOKEN = '635048049:AAHmD4MK8AgiiMEzp8ZntRl5EfbQRa7aMVg'

# ZMQ
logger.info('Creando cosas de ZMQ...')
PORT = 5551
contexto = zmq.Context()
sender = contexto.socket(zmq.REQ)
sender.connect('tcp://localhost:{}'.format(PORT))

# BOT
logger.info('Instanciando bot...')
binance_bot = telebot.TeleBot(TOKEN)

logger.info('Creando las variables de control e instanciando a los usurios previamente registrados...')
registrados = []

VARIABLESDECONTROL = {'finalizar_configuracion': False,
                      'configurar_intervalo': False,
                      'altas_cliente': False,
                      'calback_start': False,
                      'configurar': False,
                      'cancelar': False,
                      'start': False,

                      'Registrarse': False,
                      'IndexSimbol': 1}

JSON_ZMQ = {'clientes': True,
            'alta_cliente': False,
            'informacion_cliente': {},
            'altas_cliente': False,
            'chat_id': ''}

sender.send_json(json.dumps(JSON_ZMQ))
USERS = sender.recv().decode().split(',')
CONTROL_DE_USUARIOS = {}
for USER in USERS:
    CHAT_ID = int(USER)
    CONTROL_DE_USUARIOS[CHAT_ID] = {}
    CONTROL_DE_USUARIOS[CHAT_ID]['Id_chat'] = CHAT_ID
    CONTROL_DE_USUARIOS[CHAT_ID]['activo'] = 1
    CONTROL_DE_USUARIOS[CHAT_ID]['VC'] = VARIABLESDECONTROL

del USERS
JSON_ZMQ['clientes'] = False

ALL_SIMBOL = binance.get_symbols()
INTERVALOS = ['1m', '5m', '10m', '30m']

MARKUP_REGISTRO = tools.make_button_of_list(['Registrarse'])
MARKUP_CONFIGRACION = tools.make_buttons_of_dict({'Configurar una notificacion': 'Configurar',
                                                  'Mis altas': 'Altas'})
logger.info('Creando el catalogo de botones.    ')
MARKUP_ALL_SIMBOL = tools.make_many_markups_from_list(ALL_SIMBOL, 4, 5)
for i in MARKUP_ALL_SIMBOL:
    MARKUP_ALL_SIMBOL[i] = tools.add_button_cancel(MARKUP_ALL_SIMBOL[i], estructure={'Cancelar': 'start'})
MARKUP_INTERVALOS = tools.add_button_cancel(tools.make_button_of_list(INTERVALOS), estructure={'Cancelar': 'start'})
MARKUP_HOME = tools.make_buttons_of_dict({'Ir a inicio': 'start'})
logger.info('Todo listo para trabajar n.n!.')
ACTIVE_CHAT = []


@binance_bot.message_handler(commands=['start'])
def start(message):
    chat_id, message_id = tools.get_chat_id_and_message_id(message)

    logger.info('Iniciando bot con {}'.format(chat_id))
    global registrados
    JSON_ZMQ['clientes'] = True
    sender.send_json(json.dumps(JSON_ZMQ))
    clientes = sender.recv()
    clientes = clientes.decode()
    users = clientes.split(',')
    if not (str(chat_id) in users):
        tools.send_message_from_bot(binance_bot, chat_id, message_id, texts_out.REGISTRO, MARKUP_REGISTRO)
    else:
        tools.send_message_from_bot(binance_bot, chat_id, message_id,
                                    texts_out.WEOLCOMETOBACK, MARKUP_CONFIGRACION)
    JSON_ZMQ['clientes'] = False


@binance_bot.callback_query_handler(func=lambda message: message.data == 'start')
def callback_start(message):
    chat_id, message_id = tools.get_chat_id_and_message_id(message)
    logger.info('reiniciando bot con {}'.format(chat_id))
    for key in CONTROL_DE_USUARIOS[chat_id]['VC']:
        if isinstance(CONTROL_DE_USUARIOS[chat_id]['VC'][key], bool) and key != 'calback_start':
            CONTROL_DE_USUARIOS[chat_id]['VC'][key] = False
    if not CONTROL_DE_USUARIOS[chat_id]['VC']['calback_start']:
        CONTROL_DE_USUARIOS[chat_id]['VC']['calback_start'] = True
        tools.send_message_from_bot(binance_bot, chat_id, message_id,
                                    texts_out.WEOLCOMETOBACK, MARKUP_CONFIGRACION)


@binance_bot.callback_query_handler(func=lambda message: message.data == 'Configurar')
def configurar(message):
    chat_id, message_id = tools.get_chat_id_and_message_id(message)
    logger.info('configurando bot con {}'.format(chat_id))
    CONTROL_DE_USUARIOS[chat_id]['VC']['calback_start'] = False
    CONTROL_DE_USUARIOS[chat_id]['VC']['finalizar_configuracion']  = False
    if not CONTROL_DE_USUARIOS[chat_id]['VC']['configurar']:
        CONTROL_DE_USUARIOS[chat_id]['VC']['configurar'] = True
        tools.send_message_from_bot(binance_bot, chat_id, message_id,
                                    texts_out.SELECCCION_DE_SIMBOLO,
                                    MARKUP_ALL_SIMBOL[CONTROL_DE_USUARIOS[chat_id]['VC']['IndexSimbol']])


@binance_bot.callback_query_handler(func=lambda message: message.data in ALL_SIMBOL)
def configurar_intervalo(message):
    chat_id, message_id = tools.get_chat_id_and_message_id(message)
    logger.info('Configurando intervalo en bot con {}'.format(chat_id))
    CONTROL_DE_USUARIOS[chat_id]['VC']['configurar'] = False
    if not CONTROL_DE_USUARIOS[chat_id]['VC']['configurar_intervalo']:
        CONTROL_DE_USUARIOS[chat_id]['VC']['configurar_intervalo'] = True
        CONTROL_DE_USUARIOS[chat_id]['instrumento'] = message.data
        tools.send_message_from_bot(binance_bot, chat_id, message_id,
                                    texts_out.SELECCION_INTERVALO, MARKUP_INTERVALOS)


@binance_bot.callback_query_handler(func=lambda message: message.data == 'Registrarse')
def registro(message):
    chat_id, message_id = tools.get_chat_id_and_message_id(message)
    CONTROL_DE_USUARIOS[chat_id] = {}
    CONTROL_DE_USUARIOS[chat_id]['Id_chat'] = chat_id
    CONTROL_DE_USUARIOS[chat_id]['activo'] = 1
    tools.send_message_from_bot(binance_bot, chat_id, message_id, texts_out.CONFIRMATION, MARKUP_CONFIGRACION)


@binance_bot.callback_query_handler(func=lambda message: message.data in INTERVALOS)
def finalizar_configuracion(message):
    chat_id, message_id = tools.get_chat_id_and_message_id(message)
    logger.info('finalizando configuracion de bot con {}'.format(chat_id))
    CONTROL_DE_USUARIOS[chat_id]['VC']['configurar_intervalo'] = False
    if not CONTROL_DE_USUARIOS[chat_id]['VC']['finalizar_configuracion']:
        CONTROL_DE_USUARIOS[chat_id]['VC']['finalizar_configuracion'] = True
        CONTROL_DE_USUARIOS[chat_id]['intervalo'] = message.data
        JSON_ZMQ['alta_cliente'] = True
        JSON_ZMQ['informacion_cliente'] = CONTROL_DE_USUARIOS[chat_id]
        sender.send_json(json.dumps(JSON_ZMQ))
        resp = sender.recv().decode()
        if resp == 'ok':
            mensage = texts_out.FINALIZACION_DE_REGISTRO.format(CONTROL_DE_USUARIOS[chat_id]['instrumento'],
                                                                CONTROL_DE_USUARIOS[chat_id]['intervalo'])
            tools.send_message_from_bot(binance_bot, chat_id, message_id, mensage, MARKUP_HOME)
        JSON_ZMQ['alta_cliente'] = False


@binance_bot.callback_query_handler(func=lambda message: message.data == 'Anterior')
def pag_anterior(message):
    chat_id, message_id = tools.get_chat_id_and_message_id(message)
    CONTROL_DE_USUARIOS[chat_id]['VC']['configurar'] = False
    if CONTROL_DE_USUARIOS[chat_id]['VC']['IndexSimbol'] == min(MARKUP_ALL_SIMBOL):
        CONTROL_DE_USUARIOS[chat_id]['VC']['IndexSimbol'] = max(MARKUP_ALL_SIMBOL)
    elif CONTROL_DE_USUARIOS[chat_id]['VC']['IndexSimbol'] > min(MARKUP_ALL_SIMBOL):
        CONTROL_DE_USUARIOS[chat_id]['VC']['IndexSimbol'] -= 1
    configurar(message)


@binance_bot.callback_query_handler(func=lambda message: message.data == 'Siguiente')
def pag_siguiente(message):
    chat_id, message_id = tools.get_chat_id_and_message_id(message)
    CONTROL_DE_USUARIOS[chat_id]['VC']['configurar'] = False
    if CONTROL_DE_USUARIOS[chat_id]['VC']['IndexSimbol'] == max(MARKUP_ALL_SIMBOL):
        CONTROL_DE_USUARIOS[chat_id]['VC']['IndexSimbol'] = min(MARKUP_ALL_SIMBOL)
    elif CONTROL_DE_USUARIOS[chat_id]['VC']['IndexSimbol'] < max(MARKUP_ALL_SIMBOL):
        CONTROL_DE_USUARIOS[chat_id]['VC']['IndexSimbol'] += 1
    configurar(message)


@binance_bot.callback_query_handler(func=lambda message: message.data == 'Altas')
def altas_cliente(message):
    chat_id, message_id = tools.get_chat_id_and_message_id(message)
    CONTROL_DE_USUARIOS[chat_id]['VC']['calback_start'] = False
    if not CONTROL_DE_USUARIOS[chat_id]['VC']['altas_cliente']:
        CONTROL_DE_USUARIOS[chat_id]['VC']['altas_cliente'] = True
        JSON_ZMQ['altas_cliente'] = True
        JSON_ZMQ['chat_id'] = chat_id
        sender.send_json(json.dumps(JSON_ZMQ))
        message_recv = sender.recv()
        tools.send_message_from_bot(binance_bot, chat_id, message_id, message_recv.decode(), MARKUP_HOME)


@binance_bot.callback_query_handler(func=lambda message: True)
def default(message):
    chat_id, message_id = tools.get_chat_id_and_message_id(message)
    tools.send_message_from_bot(binance_bot, chat_id, message_id, texts_out.SPAM_WARNING, MARKUP_HOME)


@binance_bot.message_handler(func=lambda message: True)
def default(message):
    chat_id, message_id = tools.get_chat_id_and_message_id(message)
    tools.send_message_from_bot(binance_bot, chat_id, message_id, texts_out.SPAM_WARNING, MARKUP_HOME)


def main():
    try:
        binance_bot.polling()
    except telebot.apihelper.ApiException:
        tools.send_message()
    except KeyboardInterrupt:
        binance_bot.stop_polling()
        binance_bot.stop_bot()
    finally:
        logger.info('Finish')


if __name__ == '__main__':
    logging.basicConfig(level=levels[level_log],
                        format='%(asctime)s - %(filename)s - %(name)s - %(message)s')

    main()
