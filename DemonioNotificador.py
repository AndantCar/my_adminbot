#!/usr/bin/python3
# -*- encoding:utf-8 -*-

import time
from datetime import datetime
from threading import Thread

from telegram_tools_bot.telegram_tools import send_message
from tools.tools_sqlite import name_database, get_all_dates, create_connection, get_name


class CheckStatus(Thread):
    def __init__(self, name, token):
        super().__init__(name=name)
        self.__working = True
        self.__notification_time = 5
        self.__token = token

    def run(self) -> None:
        print('Iniciando el demonio')
        notification = datetime.today().replace(hour=12, minute=0, second=0, microsecond=0)
        while self.__working:
            if notification <= datetime.today().replace(minute=0, second=0, microsecond=0):
                fechas = get_all_dates(create_connection(name_database))
                for fecha in fechas:
                    if fecha:
                        date_time_obj = datetime.strptime(fecha, '%Y-%m-%d')
                        hoy = datetime.today()
                        if date_time_obj.date() == hoy.date() or \
                                date_time_obj.date() == hoy.replace(day=hoy.day + 1).date():
                            for user in fechas[fecha]:
                                send_message(user, f'{get_name(create_connection(name_database), user[0])} '
                                                   f'No olvides realizar el pago de: {user[1]}', self.__token)
                notification = datetime.today().replace(day=notification.day+1,
                                                        hour=12, minute=0, second=0,
                                                        microsecond=0)
            else:
                time.sleep(0.1)
        print('Termina el proceso de chequeo')

    def end_task(self):
        self.__working = False

    def restart(self):
        self.__working = True


if __name__ == '__main__':
    TOKEN = '635048049:AAHmD4MK8AgiiMEzp8ZntRl5EfbQRa7aMVg'
    checador = CheckStatus('uno', TOKEN)
    print('iniciaido')
    checador.start()
    print('corriendo')
    try:
        while 1:
            time.sleep(0.5)
    except KeyboardInterrupt:
        checador.end_task()