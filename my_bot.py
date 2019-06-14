#!/usr/bin/python3
# -*- encoding:utf-8 -*-

import logging
import os
from copy import deepcopy

from telegram_tools_bot import TelegramBot
from tools import tools_sqlite
from tools.complementos import *

logger = logging.getLogger('BinanceBot')

BOT_DICT_FLAGS = {}
NAME_PAYMENT = ''

level_log = '2'
levels = {'1': logging.DEBUG,
          '2': logging.INFO,
          '3': logging.WARNING,
          '4': logging.ERROR,
          '5': logging.CRITICAL}

logger.info('inicializando todo lo necesario...')

TOKEN = '635048049:AAHmD4MK8AgiiMEzp8ZntRl5EfbQRa7aMVg'

# BOT
logger.info('Instanciando bot...')
payment_bot = TelegramBot(TOKEN, 'tester')
# payment_bot = telebot.TeleBot(TOKEN)

logger.info('Todo listo para trabajar n.n!.')
ACTIVE_CHAT = []


@payment_bot.message_handler(command='/start')
def start(message, message_extra: str = ''):
    print('start')
    try:
        chat_id, message_id = telegram_tools.get_chat_id_and_message_id(message, True, tools_sqlite.name_database)
    except TypeError:
        logger.warning('Error al obtener el chat_id')
    else:
        if tools_sqlite.user_exist(tools_sqlite.create_connection(tools_sqlite.name_database),
                                   chat_id):
            logger.info('Entre a el if de /staet')
            message_to_send = message_extra + MESSAGE_SALUDO_START.format(telegram_tools.get_name(message))
            telegram_tools.send_message_from_bot(payment_bot, chat_id, message_id,
                                                 message_to_send,
                                                 MARKUP_MENU_PRINCIPAL)
        else:
            logger.info('Entre al else de /staet')
            telegram_tools.send_message_from_bot(payment_bot, chat_id, message_id,
                                                 MESSAGE_NEW_USER.format(telegram_tools.get_name(message)),
                                                 MARKUP_REGISTRO)


@payment_bot.callback_query_handler('start')
def callback_start(message, chat_id, message_id):
    print('calback start')
    if tools_sqlite.user_exist(tools_sqlite.create_connection(tools_sqlite.name_database),
                               chat_id):
        message_to_send = MESSAGE_SALUDO_START.format(telegram_tools.get_name(message))
        telegram_tools.send_message_from_bot(payment_bot, chat_id, message_id,
                                             message_to_send,
                                             MARKUP_MENU_PRINCIPAL)
    else:
        telegram_tools.send_message_from_bot(payment_bot, chat_id, message_id,
                                             MESSAGE_NEW_USER.format(telegram_tools.get_name(message)),
                                             MARKUP_REGISTRO)


@payment_bot.callback_query_handler('Lista De Gastos')
def lista_de_pagos(message, chat_id, message_id):
    print('lista de pagos')
    message_to_send = MESSAGE_SALUDO_START.format(telegram_tools.get_name(message))
    telegram_tools.send_message_from_bot(payment_bot, chat_id, message_id, message_to_send,
                                         MARKUP_PAYMENT_CONFIGURATION)


@payment_bot.callback_query_handler('Registrarse')
def registro(message, chat_id, message_id):
    print('registro')
    try:
        tools_sqlite.create_user(tools_sqlite.create_connection(tools_sqlite.name_database),
                                 (telegram_tools.get_name(message), chat_id))
    except Exception as details:
        telegram_tools.send_message_from_bot(payment_bot, chat_id, message_id, str(details))
    else:
        start(message, 'Tu registro fue exitoso \n')


@payment_bot.callback_query_handler('show_list')
def show_list(message, chat_id, message_id):
    print('Show_list')
    names_payments = tools_sqlite.payments_list(tools_sqlite.create_connection(tools_sqlite.name_database), chat_id)
    if names_payments:
        payments_markup = telegram_tools.make_button_of_list(names_payments, 1, add_back_button=True,
                                                             name_comand_back='Lista De Gastos')
        telegram_tools.send_only_markup(payment_bot, chat_id, message_id, payments_markup)
        BOT_DICT_FLAGS[chat_id] = FLAG_PAYMENTS_LIST
    else:
        telegram_tools.send_message_from_bot(payment_bot, chat_id, message_id, 'Aun no hay pagos registrados',
                                             MARKUP_HOME)


@payment_bot.callback_query_handler('new_payment')
def new_payment(message, chat_id, message_id):
    print('new paymnet')
    telegram_tools.send_message_from_bot(payment_bot, chat_id, message_id, MESSAGE_ANADIR_NUEVO_PAGO)
    BOT_DICT_FLAGS[chat_id] = {FLAG_NEW_PAYMENT: deepcopy(message)}


@payment_bot.callback_query_handler('help_new_payment')
def help_new_payment(message, chat_id, message_id):
    print('help new payment')
    telegram_tools.send_message_from_bot(payment_bot, chat_id, message_id, MESSAGE_AYUDA_NEW_PAYMENT, MARKUP_HOME)


@payment_bot.callback_query_handler('help_add_date')
def help_add_date(message, chat_id, message_id):
    telegram_tools.send_message_from_bot(payment_bot, chat_id, message_id, MESSAGE_AYUDA_ADD_DATE,
                                         MARKUP_GO_LIST_PAYMENTS)


@payment_bot.callback_query_handler('Limpiar chat')
def delete_message(message, chat_id, message_id):
    print('delete_message')
    telegram_tools.delete_all_message(TOKEN, chat_id, tools_sqlite.name_database)
    tools_sqlite.delete_all_message_id_of_db(tools_sqlite.create_connection(tools_sqlite.name_database),
                                             chat_id)
    start(message)


@payment_bot.callback_query_handler('add_payment_date')
def add_payment_date(message, chat_id, message_id):
    print('add payment date')
    BOT_DICT_FLAGS[chat_id] = {FLAG_ADD_DATE: deepcopy(message)}
    telegram_tools.send_message_from_bot(payment_bot, chat_id, message_id, MESSAGE_ADD_DATE,
                                         MARKUP_GO_LIST_PAYMENTS)


@payment_bot.callback_query_handler('delete_payment')
def delete_payment(message, chat_id, message_id):
    tools_sqlite.delete_payment(tools_sqlite.create_connection(tools_sqlite.name_database),
                                chat_id, NAME_PAYMENT)
    restart_flags()
    show_list(message)


@payment_bot.callback_query_handler('do_payment')
def do_payment(message, chat_id, message_id):
    print('do payment')
    tools_sqlite.update_status(tools_sqlite.create_connection(tools_sqlite.name_database),
                               chat_id)
    telegram_tools.send_message_from_bot(payment_bot, chat_id, message_id, 'Se actualizo el estatus del pago '
                                                                           'correctamente',
                                         MARKUP_GO_LIST_PAYMENTS)


@payment_bot.message_handler('/*')
def texto_libre(message, chat_id, message_id):
    print('texto libre')
    global BOT_DICT_FLAGS, NAME_PAYMENT
    try:
        if list(BOT_DICT_FLAGS[chat_id].keys())[0] == FLAG_NEW_PAYMENT:
            tools_sqlite.create_payment(tools_sqlite.create_connection(tools_sqlite.name_database),
                                        message.text,
                                        chat_id)
            telegram_tools.delete_message(TOKEN, chat_id, message_id)
            message = BOT_DICT_FLAGS[chat_id][FLAG_NEW_PAYMENT]
            restart_flags()
            start(message)
        elif list(BOT_DICT_FLAGS[chat_id].keys())[0] == FLAG_ADD_DATE:
            resultado = tools_sqlite.add_date_of_payment(tools_sqlite.create_connection(tools_sqlite.name_database),
                                                         chat_id, message.text, NAME_PAYMENT)
            if resultado:
                telegram_tools.send_message_from_bot(payment_bot, chat_id, message_id, resultado,
                                                     MARKUP_GO_LIST_PAYMENTS)
            else:
                telegram_tools.delete_message(TOKEN, chat_id, message_id)
                message = BOT_DICT_FLAGS[chat_id][FLAG_ADD_DATE]
                restart_flags()
                start(message)
        else:
            pass
    except KeyError as details:
        print(f'Detalles key error: {details}')
        telegram_tools.delete_all_message(TOKEN, chat_id, tools_sqlite.name_database)
        telegram_tools.delete_all_message_id_of_db(tools_sqlite.create_connection(tools_sqlite.name_database),
                                                   chat_id)
        telegram_tools.send_message_from_bot(payment_bot, chat_id, message_id,
                                             'Porfavor evita hacer spam', MARKUP_HOME)
    except AttributeError as details:
        print(f'Detalles AttributeError: {details}')


@payment_bot.callback_query_handler('*')
def callback_generic(message, chat_id, message_id):
    print('callback generic')
    global BOT_DICT_FLAGS, NAME_PAYMENT
    if BOT_DICT_FLAGS[chat_id] == FLAG_PAYMENTS_LIST:
        datos = tools_sqlite.get_status_payment(tools_sqlite.create_connection(tools_sqlite.name_database),
                                                message.data, chat_id)
        try:
            status_message = MESSAGE_STATUS_PAYMENT.format(datos[0][1],
                                                           'Pagado' if datos[0][4] else 'Pendiente',
                                                           datos[0][5] if datos[0][5] else 'No definido')
            NAME_PAYMENT = datos[0][1]
            telegram_tools.send_message_from_bot(payment_bot, chat_id, message_id, status_message,
                                                 MARKUP_PAYMENT_MENU)
            NAME_PAYMENT = ''
        except IndexError:
            restart_flags()
    restart_flags()


@payment_bot.callback_query_handler('Administraar contraseñas')
def manager_passwords(message, chat_id, message_id):
    print('Administraar contraseñas')
    telegram_tools.send_message_from_bot(payment_bot, chat_id, message_id, MESSAGE_DEVELOP, MARKUP_HOME)


@payment_bot.callback_query_handler('Administrador de tareas')
def manager_tasks(message, chat_id, message_id):
    print('Administrador de tareas')
    telegram_tools.send_message_from_bot(payment_bot, chat_id, message_id, MESSAGE_DEVELOP, MARKUP_HOME)


@payment_bot.callback_query_handler('Base de datos')
def get_database(message, chat_id, message_id):
    try:
        with open(os.path.join('database', tools_sqlite.name_database), 'rb') as data:
            payment_bot.send_data(chat_id, data, 'document', MESSAGE_GET_DATABASE, MARKUP_HOME, 'HTML')
    except Exception as details:
        logger.error(f'Error al intentar enviar la base de datos.\n Detalles: {details}')


def restart_flags():
    global BOT_DICT_FLAGS, NAME_PAYMENT
    BOT_DICT_FLAGS = {}
    NAME_PAYMENT = ''


def aviso_de_mantenimiento(message='El bot entrara en mantenimiento.'):
    users = tools_sqlite.get_all_users(tools_sqlite.create_connection(tools_sqlite.name_database))
    for user in users:
        telegram_tools.send_message(user, message, TOKEN)
        telegram_tools.delete_all_message(TOKEN, user, tools_sqlite.name_database)


if __name__ == '__main__':
    print('iniciando')
    logging.basicConfig(level=logging.INFO, format='%(name)s - %(lineno)s - %(message)s')
    payment_bot.start_bot()
