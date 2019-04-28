#!/usr/bin/python3
# -*- encoding:utf-8 -*-

# import os
# import time
import logging
import telebot
import urllib3

# from DemonioNotificador import CheckStatus
# from datetime import datetime
from copy import deepcopy

# import requests
# from tools import telegram_tools
from tools import tools_sqlite
from tools.complementos import *

logger = logging.getLogger('BinanceBot')

__author__ = 'Carlos Añorve'
__version__ = '1.0'
__all__ = []

BOT_DICT_FLAGS = {}
NAME_PAYMENT = ''


level_log = '1'
levels = {'1': logging.DEBUG,
          '2': logging.INFO,
          '3': logging.WARNING,
          '4': logging.ERROR,
          '5': logging.CRITICAL}

logger.info('inicializando todo lo necesario...')

# TOKEN = '558805340:AAEHYOza2FtWwORvAtdJMzV41r7ZCyITUHM'
TOKEN = '635048049:AAHmD4MK8AgiiMEzp8ZntRl5EfbQRa7aMVg'

# BOT
logger.info('Instanciando bot...')
payment_bot = telebot.TeleBot(TOKEN)

logger.info('Todo listo para trabajar n.n!.')
ACTIVE_CHAT = []


@payment_bot.message_handler(commands=['start'])
def start(message, message_extra: str = ''):
    print('start')
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
    print('calback start')
    try:
        chat_id, message_id = telegram_tools.get_chat_id_and_message_id(message, True, tools_sqlite.name_database)
    except TypeError:
        logger.warning('Error al obtener el chat_id')
    else:
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
    print('lista de pagos')
    try:
        chat_id, message_id = telegram_tools.get_chat_id_and_message_id(message, True, tools_sqlite.name_database)
    except TypeError as details:
        logger.warning(f'Error al obtener el chat_id\nDetalles: {details}\nMessage: {message}')
    else:
        telegram_tools.send_only_markup(payment_bot, chat_id, message_id, MARKUP_PAYMENT_CONFIGURATION)


@payment_bot.callback_query_handler(func=lambda message: message.data == 'Registrarse')
def registro(message):
    print('registro')
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
    print('Show_list')
    try:
        chat_id, message_id = telegram_tools.get_chat_id_and_message_id(message, True, tools_sqlite.name_database)
    except TypeError as details:
        logger.warning(f'Error al obtener el chat_id\nDetalles: {details}')
    else:
        names_payments = tools_sqlite.payments_list(tools_sqlite.create_connection(tools_sqlite.name_database), chat_id)
        if names_payments:
            payments_markup = telegram_tools.make_button_of_list(names_payments, 1, add_back_button=True,
                                                                 name_comand_back='Lista De Gastos')
            telegram_tools.send_only_markup(payment_bot, chat_id, message_id, payments_markup)
            BOT_DICT_FLAGS[chat_id] = FLAG_PAYMEENTS_LIST
        else:
            telegram_tools.send_message_from_bot(payment_bot, chat_id, message_id, 'Aun no hay pagos registrados',
                                                 MARKUP_HOME)


# @payment_bot.callback_query_handler(func=lambda message: message.data == 'go_start')
# def go_start(message):
#     start(message)


@payment_bot.callback_query_handler(func=lambda message: message.data == 'new_payment')
def new_payment(message):
    print('new paymnet')
    try:
        chat_id, message_id = telegram_tools.get_chat_id_and_message_id(message, True, tools_sqlite.name_database)
    except TypeError:
        logger.warning('Error al obtener el chat_id')
    else:
        telegram_tools.send_message_from_bot(payment_bot, chat_id, message_id, MESSAGE_ANADIR_NUEVO_PAGO)
        BOT_DICT_FLAGS[chat_id] = {FLAG_NEW_PAYMENT: deepcopy(message)}


@payment_bot.callback_query_handler(func=lambda message: message.data == 'help_new_payment')
def help_new_payment(message):
    print('help new payment')
    try:
        chat_id, message_id = telegram_tools.get_chat_id_and_message_id(message, True, tools_sqlite.name_database)
    except TypeError:
        logger.warning('Error al obtener el chat_id')
    else:
        telegram_tools.send_message_from_bot(payment_bot, chat_id, message_id, MESSAGE_AYUDA_NEW_PAYMENT, MARKUP_HOME)


@payment_bot.callback_query_handler(func=lambda message: message.data == 'help_add_date')
def help_add_date(message):
    try:
        chat_id, message_id = telegram_tools.get_chat_id_and_message_id(message, True, tools_sqlite.name_database)
    except TypeError:
        logger.warning('Error al obtener el chat_id')
    else:
        telegram_tools.send_message_from_bot(payment_bot, chat_id, message_id, MESSAGE_AYUDA_ADD_DATE,
                                             MARKUP_GO_LIST_PAYMENTS)


@payment_bot.callback_query_handler(func=lambda message: message.data == 'Limpiar chat')
def delete_message(message):
    print('delete_message')
    try:
        chat_id, message_id = telegram_tools.get_chat_id_and_message_id(message, True, tools_sqlite.name_database)
    except TypeError:
        logger.warning('Error al obtener el chat_id')
    else:
        telegram_tools.delete_all_message(TOKEN, chat_id, tools_sqlite.name_database)
        tools_sqlite.delete_all_message_id_db(tools_sqlite.create_connection(tools_sqlite.name_database),
                                              chat_id)


@payment_bot.callback_query_handler(func=lambda message: message.data == 'add_payment_date')
def add_payment_date(message):
    print('add payment date')
    try:
        chat_id, message_id = telegram_tools.get_chat_id_and_message_id(message, True, tools_sqlite.name_database)
    except TypeError:
        logger.warning('Error al obtener el chat_id')
    else:
        BOT_DICT_FLAGS[chat_id] = {FLAG_ADD_DATE: deepcopy(message)}
        telegram_tools.send_message_from_bot(payment_bot, chat_id, message_id, MESSAGE_ADD_DATE,
                                             MARKUP_GO_LIST_PAYMENTS)


@payment_bot.callback_query_handler(func=lambda message: message.data == 'delete_payment')
def delete_payment(message):
    try:
        chat_id, message_id = telegram_tools.get_chat_id_and_message_id(message, True, tools_sqlite.name_database)
    except TypeError:
        logger.warning('Error al obtener el chat_id')
    else:
        tools_sqlite.delete_payment(tools_sqlite.create_connection(tools_sqlite.name_database),
                                    chat_id, NAME_PAYMENT)
        restart_flags()
        show_list(message)


@payment_bot.callback_query_handler(func=lambda message: message.data == 'do_payment')
def do_payment(message):
    print('do payment')
    try:
        chat_id, message_id = telegram_tools.get_chat_id_and_message_id(message, True, tools_sqlite.name_database)
    except TypeError:
        logger.warning('Error al obtener el chat_id')
    else:
        tools_sqlite.update_status(tools_sqlite.create_connection(tools_sqlite.name_database),
                                   chat_id)
        telegram_tools.send_message_from_bot(payment_bot, chat_id, message_id, 'Se actualizo el estatus del pago '
                                                                               'correctamente',
                                             MARKUP_GO_LIST_PAYMENTS)


@payment_bot.message_handler(func=lambda message: True, content_types=['text'])
def texto_libre(message):
    print('texto libre')
    global BOT_DICT_FLAGS, NAME_PAYMENT
    try:
        chat_id, message_id = telegram_tools.get_chat_id_and_message_id(message, True, tools_sqlite.name_database)
    except TypeError:
        logger.warning('Error al obtener el chat_id')
    else:
        try:
            print(BOT_DICT_FLAGS)
            print(BOT_DICT_FLAGS[chat_id])
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
            telegram_tools.delete_all_message_id_db(tools_sqlite.create_connection(tools_sqlite.name_database),
                                                    chat_id)
            telegram_tools.send_message_from_bot(payment_bot, chat_id, message_id,
                                                 'Porfavor evita hacer spam', MARKUP_HOME)
        except AttributeError as details:
            print(f'Detalles AttributeError: {details}')


@payment_bot.callback_query_handler(func=lambda message: True)
def callback_generic(message):
    print('callback generic')
    global BOT_DICT_FLAGS, NAME_PAYMENT
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
                                                               datos[0][5] if datos[0][5] else 'No definido')
                NAME_PAYMENT = datos[0][1]
                telegram_tools.send_message_from_bot(payment_bot, chat_id, message_id, status_message,
                                                     MARKUP_PAYMENT_MENU)
            except IndexError:
                restart_flags()


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
    print('Ejecutando como main')