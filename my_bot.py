#!/usr/bin/python3
# -*- encoding:utf-8 -*-

import os
import logging
import telebot
import urllib3

from datetime import datetime
from copy import deepcopy

from tools import telegram_tools
from tools import tools_sqlite
from tools.complementos import *

logger = logging.getLogger('BinanceBot')

__author__ = 'Carlos Añorve'
__version__ = '1.0'
__all__ = []


level_log = '1'
levels = {'1': logging.DEBUG,
          '2': logging.INFO,
          '3': logging.WARNING,
          '4': logging.ERROR,
          '5': logging.CRITICAL}

logger.info('inicializando todo lo necesario...')

TOKEN = '635048049:AAHmD4MK8AgiiMEzp8ZntRl5EfbQRa7aMVg'

# BOT
logger.info('Instanciando bot...')
payment_bot = telebot.TeleBot(TOKEN)

logger.info('Todo listo para trabajar n.n!.')
ACTIVE_CHAT = []


@payment_bot.message_handler(commands=['start'])
def start(message, message_extra: str = ''):
    restart_flags()
    try:
        chat_id, message_id = telegram_tools.get_chat_id_and_message_id(message, True, tools_sqlite.name_database)
    except TypeError:
        logger.warning('Error al obtener el chat_id')
    else:
        if tools_sqlite.user_exist(tools_sqlite.create_connection(tools_sqlite.name_database),
                                   chat_id):
            message_to_send = message_extra + MESSAGE_SALUDO_START.format(telegram_tools.get_name(message))
            telegram_tools.send_message_from_bot(payment_bot, chat_id, message_id,
                                                 message_to_send,
                                                 MARKUP_LISTA_DE_PAGOS)
        else:
            telegram_tools.send_message_from_bot(payment_bot, chat_id, message_id,
                                                 MESSAGE_NEW_USER.format(telegram_tools.get_name(message)),
                                                 MARKUP_REGUSTRO)


@payment_bot.callback_query_handler(func=lambda message: message.data == 'start')
def callback_start(message):
    restart_flags()
    try:
        chat_id, message_id = telegram_tools.get_chat_id_and_message_id(message, True, tools_sqlite.name_database)
    except TypeError:
        logger.warning('Error al obtener el chat_id')
    else:
        print(message)
        if tools_sqlite.user_exist(tools_sqlite.create_connection(tools_sqlite.name_database),
                                   chat_id):
            message_to_send = MESSAGE_SALUDO_START.format(telegram_tools.get_name(message))
            telegram_tools.send_message_from_bot(payment_bot, chat_id, message_id,
                                                 message_to_send,
                                                 MARKUP_LISTA_DE_PAGOS)
        else:
            telegram_tools.send_message_from_bot(payment_bot, chat_id, message_id,
                                                 MESSAGE_NEW_USER.format(telegram_tools.get_name(message)),
                                                 MARKUP_REGUSTRO)


@payment_bot.callback_query_handler(func=lambda message: message.data == 'Lista De Gastos')
def lista_de_pagos(message):
    try:
        chat_id, message_id = telegram_tools.get_chat_id_and_message_id(message, True, tools_sqlite.name_database)
    except TypeError as details:
        logger.warning(f'Error al obtener el chat_id\nDetalles: {details}\nMessage: {message}')
    else:
        telegram_tools.send_only_markup(payment_bot, chat_id, message_id, MARKUP_CONFIGRACION)


@payment_bot.callback_query_handler(func=lambda message: message.data == 'Registrarse')
def registro(message):
    try:
        chat_id, message_id = telegram_tools.get_chat_id_and_message_id(message, True, tools_sqlite.name_database)
    except TypeError:
        logger.warning('Error al obtener el chat_id')
    else:
        try:
            tools_sqlite.create_user(tools_sqlite.create_connection(tools_sqlite.name_database),
                                     (telegram_tools.get_name(message), chat_id))
        except Exception as details:
            telegram_tools.send_message_from_bot(payment_bot, chat_id, message_id, str(details))
        else:
            start(message, 'Tu registro fue exitoso \n')


@payment_bot.callback_query_handler(func=lambda message: message.data == 'show_list')
def show_list(message):
    try:
        chat_id, message_id = telegram_tools.get_chat_id_and_message_id(message, True, tools_sqlite.name_database)
    except TypeError as details:
        logger.warning(f'Error al obtener el chat_id\nDetalles: {details}')
    else:
        names_payments = tools_sqlite.payments_list(tools_sqlite.create_connection(tools_sqlite.name_database), chat_id)
        if names_payments:
            payments_markup = telegram_tools.make_button_of_list(names_payments, 1, add_back_button=True)
            telegram_tools.send_only_markup(payment_bot, chat_id, message_id, payments_markup)
            BOT_DICT_FLAGS[chat_id] = FLAG_PAYMEENTS_LIST
        else:
            telegram_tools.send_message_from_bot(payment_bot, chat_id, message_id, 'Aun no hay pagos registrados',
                                                 MARKUP_LISTA_DE_PAGOS)


# @payment_bot.callback_query_handler(func=lambda message: message.data == 'go_start')
# def go_start(message):
#     start(message)


@payment_bot.callback_query_handler(func=lambda message: message.data == 'new_payment')
def new_payment(message):
    try:
        chat_id, message_id = telegram_tools.get_chat_id_and_message_id(message, True, tools_sqlite.name_database)
    except TypeError:
        logger.warning('Error al obtener el chat_id')
    else:
        telegram_tools.send_message_from_bot(payment_bot, chat_id, message_id, MESSAGE_ANADIR_NUEVO_PAGO)
        BOT_DICT_FLAGS[chat_id] = {1: deepcopy(message)}


@payment_bot.callback_query_handler(func=lambda message: message.data == 'help_new_payment')
def help_new_payment(message):
    try:
        chat_id, message_id = telegram_tools.get_chat_id_and_message_id(message, True, tools_sqlite.name_database)
    except TypeError:
        logger.warning('Error al obtener el chat_id')
    else:
        telegram_tools.send_message_from_bot(payment_bot, chat_id, message_id, MESSAGE_AYUDA_NEW_PAYMENT, MARKUP_HOME)
        new_payment(message)


@payment_bot.callback_query_handler(func=lambda message: message.data == 'Limpiar chat')
def delete_message(message):
    try:
        chat_id, message_id = telegram_tools.get_chat_id_and_message_id(message, True, tools_sqlite.name_database)
    except TypeError:
        logger.warning('Error al obtener el chat_id')
    else:
        telegram_tools.delete_all_message(TOKEN, chat_id, tools_sqlite.name_database)


@payment_bot.message_handler(func=lambda message: True)
def texto_libre(message):
    try:
        chat_id, message_id = telegram_tools.get_chat_id_and_message_id(message, True, tools_sqlite.name_database)
    except TypeError:
        logger.warning('Error al obtener el chat_id')
    else:
        try:
            if list(BOT_DICT_FLAGS[chat_id].keys())[0] == FLAG_NEW_PAYMENT:
                tools_sqlite.create_payment(tools_sqlite.create_connection(tools_sqlite.name_database),
                                            message.text,
                                            chat_id)
                telegram_tools.delete_message(TOKEN, chat_id, message_id)
                message = BOT_DICT_FLAGS[chat_id][1]
                start(message)
            else:
                pass
        except KeyError:
            pass


@payment_bot.callback_query_handler(func=lambda message: True)
def callback_generic(message):
    print('Here')
    try:
        chat_id, message_id = telegram_tools.get_chat_id_and_message_id(message, True, tools_sqlite.name_database)
    except TypeError:
        logger.warning('Error al obtener el chat_id')
    else:
        if BOT_DICT_FLAGS[chat_id] == FLAG_PAYMEENTS_LIST:
            datos = tools_sqlite.get_status_payment(tools_sqlite.create_connection(tools_sqlite.name_database),
                                                    message.data, chat_id)
            try:
                status_message = MESSAGE_STATUS_PAYMENT.format(datos[0][1],
                                                               'Pagado' if datos[0][4] else 'Pendiente',
                                                               datos[0][6] if datos[0][6] else 'No definido')
                telegram_tools.send_message_from_bot(payment_bot, chat_id, message_id, status_message,
                                                     MARKUP_HOME_AND_BACK)
            except IndexError:
                restart_flags()


def aviso_de_mantenimiento():
    users = tools_sqlite.get_all_users(tools_sqlite.create_connection(tools_sqlite.name_database))
    for user in users:
        telegram_tools.send_message(user, 'El bot entrara en mantenimiento.', TOKEN)
        telegram_tools.delete_all_message(TOKEN, user, tools_sqlite.name_database)


def main(estatus=''):
    """

    :param estatus:
    :return:
    """
    print(f'Status: {estatus}')
    # try:
    try:
        payment_bot.polling(none_stop=True, timeout=20)
    except telebot.apihelper.ApiException:
        # telegram_tools.send_message()
        print('nada')
    except KeyboardInterrupt:
        payment_bot.stop_polling()
        payment_bot.stop_bot()
    finally:
        try:
            aviso_de_mantenimiento()
        except Exception as details:
            logger.error(f'Error al enviar el aviso: {details}')
        logger.info('Finish')
    # except urllib3.exceptions.MaxRetryError:
    #     main('retinteno')


if __name__ == '__main__':
    logging.basicConfig(level=levels[level_log],
                        format='%(asctime)s - %(lineno)d - %(name)s - %(message)s',
                        filename=f'My_admin_log{datetime.today().date()}.log')
    if not os.path.exists('database'):
        os.mkdir('database')
    if not os.path.exists(tools_sqlite.name_database):
        tools_sqlite.make_database_and_tables()
    main()
