#!/usr/bin/python3
# -*- encoding:utf-8 -*-

import datetime
import logging
import queue
import threading
import time

import requests
try:
    from requests.packages.urllib3 import fields
    format_header_param = fields.format_header_param
except ImportError:
    format_header_param = None

from telegram_tools_bot import sqlite_tools
from telegram_tools_bot import telegram_tools
from telegram_tools_bot import telegram_types
from tools import tools_sqlite
from telebot import util

logger = logging.getLogger('my_requests')

# token_bot = os.getenv('token')
base_url = 'https://api.telegram.org/bot{}/{}'


class WorkerProcess(threading.Thread):
    def __init__(self, name, queue_messages, commands_message_handler, commands_qquery_handler, timeout):
        super().__init__(name=f'{name}_WorkerProcess')
        self.__name = f'{name}_WorkerProcess'
        self.queue_message = queue_messages
        self.__stop = threading.Event()
        self.timeout = datetime.timedelta(seconds=timeout)
        self.commands_message_handler = commands_message_handler
        self.commands_query_handler = commands_qquery_handler

    def run(self) -> None:
        while not self.__stop.is_set():
            if not self.queue_message.empty():
                message = self.queue_message.get()
                self.process_new_update(message)
            time.sleep(.25)

    def stop(self):
        if not self.__stop.is_set():
            self.__stop.set()

    def process_new_update(self, update):
        new_messages = []
        edited_new_messages = []
        new_channel_posts = []
        new_edited_channel_posts = []
        new_inline_querys = []
        new_chosen_inline_results = []
        new_callback_querys = []
        new_shipping_querys = []
        new_pre_checkout_querys = []
        if update.message:
            new_messages.append(update.message)
        if update.edited_message:
            edited_new_messages.append(update.edited_message)
        if update.channel_post:
            new_channel_posts.append(update.channel_post)
        if update.edited_channel_post:
            new_edited_channel_posts.append(update.edited_channel_post)
        if update.inline_query:
            new_inline_querys.append(update.inline_query)
        if update.chosen_inline_result:
            new_chosen_inline_results.append(update.chosen_inline_result)
        if update.callback_query:
            new_callback_querys.append(update.callback_query)
        if update.shipping_query:
            new_shipping_querys.append(update.shipping_query)
        if update.pre_checkout_query:
            new_pre_checkout_querys.append(update.pre_checkout_query)
        if new_messages:
            self.process_new_messages(new_messages)
        if new_callback_querys:
            self.process_new_callback_query(new_callback_querys)

    def process_new_messages(self, new_messages):
        for message in new_messages:
            if self.__check_date(message):
                comand_func = self.get_func_work(message.text, 'message')
                if comand_func:
                    chat_id, message_id = telegram_tools.get_chat_id_and_message_id(message, True,
                                                                                    tools_sqlite.name_database)
                    self.__exec_func(comand_func['function'], message, chat_id, message_id)

    def process_new_callback_query(self, new_callback_query):
        for message in new_callback_query:
            comand_func = self.get_func_work(message.data, 'query')
            if comand_func:
                chat_id, message_id = telegram_tools.get_chat_id_and_message_id(message, True,
                                                                                tools_sqlite.name_database)
                self.__exec_func(comand_func['function'], message, chat_id, message_id)

    def get_func_work(self, command, type_message):
        func = self.commands_message_handler.get(command)
        func = func if func else self.commands_query_handler.get(command)
        if func:
            return func
        else:
            if type_message == 'message':
                func = self.commands_message_handler.get('/*')
            elif type_message == 'query':
                func = func if func else self.commands_query_handler.get('*')
            else:
                func = None
            return func

    @staticmethod
    def __exec_func(func, *args, **kwargs):
        func(*args, **kwargs)

    def __check_date(self, message):
        hora_mensaje = self.get_date(message)
        return (datetime.datetime.today() - hora_mensaje) < self.timeout

    @staticmethod
    def get_date(message):
        try:
            date = message.date
        except AttributeError:
            return True
        else:
            date = datetime.datetime.fromtimestamp(date)
            hoy = datetime.datetime.today()
            date = date.replace(year=hoy.year, month=hoy.month, day=hoy.day)
            return date


class WorkerGetUpdates(threading.Thread):
    def __init__(self, name, queue_message, token):
        super().__init__(name=f'{name}_WorkerGetUpdate')
        self.__name = f'{name}_WorkerGetUpdate'
        self.db = sqlite_tools.SqliteTools(self.__name)
        self.__logger = logging.getLogger(self.__name)
        self.__stop = threading.Event()
        self.__token = token
        self.__sesion = requests.Session()
        self.last_data = self.db.get_last_id_update()
        self.queue_message = queue_message

    def run(self) -> None:
        while not self.__stop.is_set():
            update = self.__get_updates()
            if update['ok']:
                datas = {e['update_id']: e for e in update['result']}
            else:
                datas = {}
                self.__logger.debug('Sin datos')
            for last_data_id in datas:
                if last_data_id > self.last_data:
                    self.last_data = last_data_id
                    self.__proccess_new_message(datas[last_data_id])
            time.sleep(1)
        self.db.insert_data_last_id_update(self.last_data)

    def stop(self):
        if not self.__stop.is_set():
            self.__stop.set()
        else:
            self.__logger.warning('El hilo pfue pausado previamente.')

    def control_flow(self):
        while self.is_alive():
            try:
                time.sleep(.25)
            except KeyboardInterrupt:
                break
        self.stop()

    def __get_updates(self):
        return self.__sesion.get(base_url.format(self.__token, 'getUpdates')).json()

    def __proccess_new_message(self, message):
        message = telegram_types.Update.de_json(message)
        self.queue_message.put(message)


class TelegramBot:
    def __init__(self, token, name, timeout=15):
        self.__logger = logging.getLogger(__name__)
        self.queue_message = queue.Queue()
        self.__name = name
        self.__token = token
        self.timeout = timeout
        self.worker_get_update = None
        self.worker_process = None
        self.commands_message_handler = {}
        self.commands_query_handler = {}

    # Metodos de control del hilo
    def make_workers(self):
        self.worker_get_update = WorkerGetUpdates(self.__name, self.queue_message, self.__token)
        self.worker_process = WorkerProcess(self.__name, self.queue_message, self.commands_message_handler,
                                            self.commands_query_handler, self.timeout)

    def start_bot(self):
        self.make_workers()
        self.worker_get_update.start()
        self.worker_process.start()
        self.control_flow()

    def control_flow(self):
        while self.worker_get_update.is_alive() and self.worker_process.is_alive():
            try:
                time.sleep(.25)
            except KeyboardInterrupt:
                break
            except Exception as details:
                self.__logger.error('Un error desconocido ocurrio en la ejecucion del bot probocando al salida.\n'
                                    f'Detalles: {details}')
                break
        self.worker_get_update.stop()
        self.worker_process.stop()

    def get_message(self):
        if not self.queue_message.empty():
            return self.queue_message.get()

    def stop_bot(self):
        self.worker_get_update.stop()
        self.worker_process.stop()

    # Metodos decoradores de funciones
    def message_handler(self, command, func=None):
        def decorator(handler):
            handler_dict = self.__build_handler_dict(handler, func=func)
            self.__add_new_command(command, handler_dict, 'message')
            return handler

        return decorator

    def callback_query_handler(self, command, func=None):
        def decorator(handler):
            handler_dict = self.__build_handler_dict(handler,
                                                     func=func if func else lambda message: message.data == command)
            self.__add_new_command(command, handler_dict, 'query')
            return handler

        return decorator

    # Metodos privados para la clase
    @staticmethod
    def __build_handler_dict(handler, **filters):
        return {
            'function': handler,
            'filters': filters
        }

    def __add_new_command(self, command, handler_dict, type_comand):
        if type_comand == 'message':
            self.commands_message_handler[command] = handler_dict
        elif type_comand == 'query':
            self.commands_query_handler[command] = handler_dict

    # Metodos funcionales para interfasear con la api
    def edit_message_text(self, text, chat_id=None, message_id=None, inline_message_id=None, parse_mode=None,
                          disable_web_page_preview=None, reply_markup=None):
        method_url = r'editMessageText'
        params = {'text': text}
        if chat_id:
            params['chat_id'] = chat_id
        if message_id:
            params['message_id'] = message_id
        if inline_message_id:
            params['inline_message_id'] = inline_message_id
        if parse_mode:
            params['parse_mode'] = parse_mode
        if disable_web_page_preview:
            params['disable_web_page_preview'] = disable_web_page_preview
        if reply_markup:
            params['reply_markup'] = self._convert_markup(reply_markup)
        return self.__make_requests(self.__token, method_url, params, method='post')

    def edit_message_reply_markup(self, chat_id=None, message_id=None, inline_message_id=None, reply_markup=None):
        method_url = r'editMessageReplyMarkup'
        params = {}
        if chat_id:
            params['chat_id'] = chat_id
        if message_id:
            params['message_id'] = message_id
        if inline_message_id:
            params['inline_message_id'] = inline_message_id
        if reply_markup:
            params['reply_markup'] = self._convert_markup(reply_markup)
        return self.__make_requests(self.__token, method_url, params=params)

    def delete_message(self, chat_id, message_id):
        method_url = r'deleteMessage'
        params = {'chat_id': chat_id, 'message_id': message_id}
        return self.__make_requests(self.__token, method_url, params=params)

    def send_message(self, chat_id, text, disable_web_page_preview=None, reply_to_message_id=None, reply_markup=None,
                     parse_mode=None, disable_notification=None):
        method_url = r'sendMessage'
        payload = {'chat_id': str(chat_id), 'text': text}
        if disable_web_page_preview:
            payload['disable_web_page_preview'] = disable_web_page_preview
        if reply_to_message_id:
            payload['reply_to_message_id'] = reply_to_message_id
        if reply_markup:
            payload['reply_markup'] = self._convert_markup(reply_markup)
        if parse_mode:
            payload['parse_mode'] = parse_mode
        if disable_notification:
            payload['disable_notification'] = disable_notification
        return self.__make_requests(self.__token, method_url, params=payload, method='post')

    def send_data(self, chat_id, data, data_type, reply_to_message_id=None, reply_markup=None, parse_mode=None,
                  disable_notification=None, timeout=None, caption=None):
        method_url = self.__get_method_by_type(data_type)
        payload = {'chat_id': chat_id}
        files = None
        if not util.is_string(data):
            files = {data_type: data}
        else:
            payload[data_type] = data
        if reply_to_message_id:
            payload['reply_to_message_id'] = reply_to_message_id
        if reply_markup:
            payload['reply_markup'] = self._convert_markup(reply_markup)
        if parse_mode and data_type == 'document':
            payload['parse_mode'] = parse_mode
        if disable_notification:
            payload['disable_notification'] = disable_notification
        if timeout:
            payload['connect-timeout'] = timeout
        if caption:
            payload['caption'] = caption
        return self.__make_requests(self.__token, method_url, params=payload, files=files, method='post')

    # Metodos auxiliares para los metodos que interfasean con la API de telegram
    def __make_requests(self, token, method_url, params=None, files=None, method='get'):
        ses = requests.Session()
        if files and format_header_param:
            fields.format_header_param = self._no_encode(format_header_param)
        result = ses.request(method, url=base_url.format(token, method_url), params=params, files=files).json()
        if self.__request_is_ok(result):
            self.__logger.info(f'Se ejecuto correctamente el metodo {method_url}')
            result = result.get('result')
            if result:
                return telegram_types.Message.de_json(result)
            else:
                raise MethodRequestError(method_url)
        else:
            self.__logger.warning(f'Error al ejecutar el metodo {method_url}: {result}')
            raise MethodRequestError(method_url)

    @staticmethod
    def _convert_markup(markup):
        try:
            return markup.to_json()
        except Exception as details:
            return markup

    @staticmethod
    def __request_is_ok(response):
        """
        Verifica que la espuesta de la solicitud sea satisfactoria.

        Argss:
            response(requests.models.Response): Respuesta obtenida de la solicitud.

        Returns:
            None
        """
        if response.get('ok'):
            logger.debug('La solisutd se ejecuto correctamente.')
            return True
        else:
            logger.warning('Algun error ocurrio en la solicitud.\n'
                           'Error: {}'.format(response))
            raise MethodRequestError('Codigo de error: {}'.format(response))

    @staticmethod
    def _no_encode(func):
        def wrapper(key, val):
            if key == 'filename':
                return u'{0}={1}'.format(key, val)
            else:
                return func(key, val)

        return wrapper

    @staticmethod
    def __get_method_by_type(data_type):
        if data_type == 'document':
            return r'sendDocument'
        if data_type == 'sticker':
            return r'sendSticker'


class MethodRequestError(Exception):
    def __init__(self, message):
        super(Exception, self).__init__(message)
