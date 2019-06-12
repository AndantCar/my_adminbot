#!/usr/bin/python3
# -*- encoding:utf-8 -*-

import datetime
import logging
import os
import queue
import threading
import time

import requests

from my_request import sqlite_tools
from my_request import telegram_tools
from my_request import telegram_types

logger = logging.getLogger('my_requests')

# token_bot = os.getenv('token')
base_url = 'https://api.telegram.org/bot{}/{}'


class TelegramTools:
    def __init__(self):
        pass


class WorkerProcess(threading.Thread):
    def __init__(self, name, queue_messages, commands_message_handler, commands_qquery_handler, timeout):
        super().__init__(name=f'{name}_WorkerProcess')
        self.__name = f'{name}_WorkerProcess'
        self.queue_message = queue_messages
        self.__stop = threading.Event()
        self.timeout = datetime.timedelta(seconds=timeout)
        self.commands_message_handler = commands_message_handler
        self.commands_qquery_handler = commands_qquery_handler

    def run(self) -> None:
        while not self.__stop.is_set():
            if not self.queue_message.empty():
                message = self.queue_message.get()
                self.process_new_update(message)

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
                comand_func = self.get_func_work(message.text)
                if comand_func:
                    self.__exec_func(comand_func['function'], message)

    def process_new_callback_query(self, new_callback_query):
        for message in new_callback_query:
            if self.__check_date(message):
                comand_func = self.get_func_work(message.data)
                if comand_func:
                    self.__exec_func(comand_func['function'], message)

    def get_func_work(self, command):
        func = self.commands_message_handler.get(command)
        func = func if func else self.commands_qquery_handler.get(command)
        if func:
            return func
        else:
            func = self.commands_message_handler.get('*')
            func = func if func else self.commands_qquery_handler.get('*')
            return func

    @staticmethod
    def __exec_func(func, *args, **kwargs):
        func(*args, **kwargs)

    def __check_date(self, message):
        hora_mensaje = datetime.datetime.fromtimestamp(message.date)
        return (datetime.datetime.today() - hora_mensaje) < self.timeout


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

    def make_workers(self):
        self.worker_get_update = WorkerGetUpdates(self.__name, self.queue_message, self.__token)
        self.worker_process = WorkerProcess(self.__name, self.queue_message, self.commands_message_handler,
                                            self.commands_query_handler, self.timeout)

    def start(self):
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
        self.worker_get_update.stop()
        self.worker_process.stop()

    def get_message(self):
        if not self.queue_message.empty():
            return self.queue_message.get()

    def message_handler(self, command=None, func=None):
        def decorator(handler):
            handler_dict = self.__build_handler_dict(handler, func=func)
            self.__add_new_command(command, handler_dict, 'message')
            return handler

        return decorator

    def callback_query_handler(self, command=None, func=None):
        def decorator(handler):
            handler_dict = self.__build_handler_dict(handler, func=func)
            self.__add_new_command(command, handler_dict, 'query')
            return handler

        return decorator

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

    # def send_message(self, chat_id, message, parse_mode='HTML'):
    #     """
    #     Envia un mensaje al chat espesificado a travez de la api de telegram bot
    #
    #     Args:
    #         chat_id(int, str): id que identifica al chat.
    #         message(str): Mensaje ue se quiere enviar.
    #         token(str): token espesifico del bot que se quiere utilizar
    #         parse_mode(str): Tipo de parser que se utilizara para enviar el mensaje.
    #
    #     Returns:
    #          None
    #     """
    #     method_url = r'sendMessage'
    #     params = {'chat_id': str(chat_id), 'text': message, 'parse_mode': parse_mode}
    #     try:
    #         response = self.make_requests(self.__token, method_url, params)
    #     except Exception as details:
    #         logger.warning('Error al intentar enviar el mensaje.\n'
    #                        'Details: {}'.format(details))
    #         raise MethodRequestError(details)
    #     else:
    #         self.request_is_ok(response)
    #     return response

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
        result = self.make_requests(self.__token, method_url, params)
        if result:
            return telegram_types.Message.de_json(result)

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
        return self.make_requests(self.__token, method_url, params=params)

    def delete_message(self, chat_id, message_id):
        method_url = r'deleteMessage'
        params = {'chat_id': chat_id, 'message_id': message_id}
        return self.make_requests(self.__token, method_url, params=params)

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
        result = self.make_requests(self.__token, method_url, params=payload, method='get')
        if result:
            return telegram_types.Message.de_json(result)

    def make_requests(self, token, method_url, params, method='get'):
        if method.lower() == 'get':
            result = requests.get(url=base_url.format(token, method_url), params=params).json()
        elif method.lower() == 'post':
            result = requests.post(url=base_url.format(token, method_url), params=params).json()
        else:
            return None
        if result['ok']:
            self.__logger.info(f'Se ejecuto correctamente el metodo {method_url}')
            return result.get('result')
        else:
            self.__logger.warning(f'Error al ejecutar el metodo {method_url}: {result}')

    @staticmethod
    def _convert_markup(markup):
        if isinstance(markup, telegram_types.JsonSerializable):
            return markup.to_json()
        return markup

    @staticmethod
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


class MethodRequestError(Exception):
    def __init__(self, message):
        super(Exception, self).__init__(message)

