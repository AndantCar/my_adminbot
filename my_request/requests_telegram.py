#!/usr/bin/python3
# -*- encoding:utf-8 -*-

import os
import queue
import time

import requests
import logging
import threading

logger = logging.getLogger('my_requests')

token = os.getenv('token')
base_url = 'https://api.telegram.org/bot{}/{}'

queue_message = queue.Queue()


def send_message(chat_id, message, token_bot, parse_mode='HTML'):
    """
    Envia un mensaje al chat espesificado a travez de la api de telegram bot

    Args:
        chat_id(int, str): id que identifica al chat.
        message(str): Mensaje ue se quiere enviar.
        token_bot(str): token espesifico del bot que se quiere utilizar
        parse_mode(str): Tipo de parser que se utilizara para enviar el mensaje.

    Returns:
         None
    """
    params = {'chat_id': str(chat_id), 'text': message, 'parse_mode': parse_mode}
    try:
        response = requests.get(url=base_url.format(token_bot, 'sendMessage'), params=params).json()
    except Exception as details:
        logger.warning('Error al intentar enviar el mensaje.\n'
                       'Details: {}'.format(details))
        raise MethodRequestError(details)
    else:
        request_is_ok(response)
    return response


def request_is_ok(response):
    """
    Verifica que la espuesta de la solicitud sea satisfactoria.

    Argss:
        response(requests.models.Response): Respuesta obtenida de la solicitud.

    Returns:
        None
    """
    if response['ok']:
        logger.debug('La solisutd se ejecuto correctamente.')
        return True
    else:
        logger.warning('Algun error ocurrio en la solicitud.\n'
                       'Error: {}'.format(response))
        raise MethodRequestError('Codigo de error: {}'.format(response))


class Updates(threading.Thread):
    def __init__(self, name):
        super().__init__(name=name)
        self.__logger = logging.getLogger(name)
        self.__name = name
        self.__stop = threading.Event()
        self.__token = os.getenv('token')
        self.last_data = 0

    def run(self) -> None:
        while not self.__stop.is_set():
            update = self.get_updates()
            datas = {}
            if update:
                datas = {e['update_id']: e for e in update['result']}
                try:
                    last_data_id = max(datas)
                except ValueError:
                    last_data_id = -1
            else:
                self.__logger.warning('SIn datos')
                last_data_id = -1
            if last_data_id > self.last_data:
                self.last_data = last_data_id
                queue_message.put(datas[last_data_id])
                send_message(datas[last_data_id]['message']['chat']['id'], datas[last_data_id]['message']['text'],
                             token)

    def stop(self):
        if not self.__stop.is_set():
            self.__stop.set()
        else:
            self.__logger.warning('El hilo pfue pausado previamente.')

    def get_updates(self):
        return requests.get(base_url.format(self.__token, 'getUpdates')).json()


class RepliMessage(threading.Thread):
    def __init__(self, name):
        super().__init__(name=name)
        self.__logger = logging.getLogger(name)
        self.__stop = threading.Event()

    def run(self) -> None:
        while not self.__stop.is_set():
            if not queue_message.empty():
                message = queue_message.get()

    def stop(self):
        if not self.__stop.is_set():
            self.__stop.set()
        else:
            self.__logger.warning('El hilo fue detenido previamente')


class MethodRequestError(Exception):
    def __init__(self, message):
        super(Exception, self).__init__(message)


logging.basicConfig(level=logging.INFO)
logger.info('Iniciando')
hilo = Updates('Hilo 1')
hilo.start()
while hilo.is_alive():
    try:
        time.sleep(.1)
    except KeyboardInterrupt:
        hilo.stop()

# TODO hacer una base de datos para almacenar la informacion.
# TODO ALmacenar ultimo id de actualizacion.
# TODO ALmacenar la hoay fecha de la ultima actualizacion.
# TODO Crear un usuario cuando se inicie un nuevo chat.
