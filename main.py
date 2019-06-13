
import os
import telebot
import logging
import urllib3

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
        my_bot.payment_bot.start_bot()
    except Exception as detils:
        my_bot.aviso_de_mantenimiento(f'Error en la api del bot. Detalles: {detils}')
    except KeyboardInterrupt:
        my_bot.aviso_de_mantenimiento()
        logger.info('Finish')
    finally:
        my_bot.payment_bot.stop_bot()


if __name__ == '__main__':
    try:
        print('Inicializando el bot')
        logging.basicConfig(level=levels[level_log],
                            format='%(asctime)s - %(lineno)d - %(name)s - %(message)s')
        #                    filename=f'My_admin_log{datetime.today().date()}.log')
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
        my_bot.payment_bot.stop_bot()
        print('Me rompi aqui')