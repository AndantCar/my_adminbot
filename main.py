
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
        my_bot.aviso_de_mantenimiento()
        logger.info('Finish')
    except (urllib3.exceptions.MaxRetryError, urllib3.exceptions.ProtocolError) as details:
        print(f'Errror 1: {details}')
    except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout) as details:
        print(f'Errror 2: {details}')
    except OSError as details:
        print(f'Errror 3: {details}')
    finally:
        my_bot.payment_bot.stop_bot()


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