
import os
import time
import telebot
import logging
import urllib3

from datetime import datetime

import requests
from tools import tools_sqlite
from DemonioNotificador import CheckStatus
import my_bot

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

logger.info('Todo listo para trabajar n.n!.')
ACTIVE_CHAT = []


def main(estatus='Iniciando'):
    """

    :param estatus:
    :return:
    """
    print(f'Status: {estatus}')
    try:
        my_bot.payment_bot.polling()
    except telebot.apihelper.ApiException:
        my_bot.payment_bot.stop_bot()
        my_bot.aviso_de_mantenimiento('Error en la api del bot')
    except KeyboardInterrupt:
        my_bot.payment_bot.stop_bot()
        my_bot.aviso_de_mantenimiento()
        logger.info('Finish')
    except (urllib3.exceptions.MaxRetryError, requests.exceptions.ReadTimeout) as details:
        my_bot.payment_bot.stop_bot()
        my_bot.aviso_de_mantenimiento(details)
        main('retinteno')
    except (requests.exceptions.ConnectionError,
            OSError,
            urllib3.exceptions.ProtocolError) as details:
        my_bot.payment_bot.stop_bot()
        my_bot.payment_bot = telebot.TeleBot(my_bot.TOKEN)
        time.sleep(20)
        my_bot.aviso_de_mantenimiento(str(details))
        main('retinteno por falta de internet')


if __name__ == '__main__':
    try:
        print('Inicializando el bot')
        logging.basicConfig(level=levels[level_log],
                            format='%(asctime)s - %(lineno)d - %(name)s - %(message)s',
                            filename=f'My_admin_log{datetime.today().date()}.log')
        if not os.path.exists('database'):
            os.mkdir('database')
        if not os.path.exists(tools_sqlite.name_database):
            tools_sqlite.make_database_and_tables()
        check_dates = CheckStatus('My_admin', TOKEN)
        check_dates.start()
        main()
        check_dates.end_task()
        print('Finalizo el proceso')
    except Exception:
        print('Me rompi aqui')