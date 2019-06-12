#!/usr/bin/python3
# -*- encoding:utf-8 -*-

import logging
import queue
import sqlite3
import threading
import time


class QueueHandler(logging.Handler):
    def __init__(self, log_queue):
        super().__init__()
        self.__log_queue = log_queue

    def emit(self, record):
        self.__log_queue.put(record)


class DaemonLogger(threading.Thread):
    def __init__(self, new_logger, name_thread='DaemonLogger'):
        super().__init__(name=name_thread)
        self.__logger = logging.getLogger(name_thread)
        self.logger = new_logger
        self.__log_queue = queue.Queue()
        self.__stop = threading.Event()
        self.queue_handler = QueueHandler(self.__log_queue)
        self.__format = None
        self.queue_handler.setFormatter(self.format)
        self.logger.addHandler(self.queue_handler)
        self.table = Table(f'{name_thread}.db', self.logger.name, {'fecha': 'text', 'level': 'text', 'mensaje': 'text'})
        self.start()

    def run(self):
        while not self.__stop.is_set():
            if not self.__log_queue.empty():
                msg = self.__log_queue.get()
                msg = self.queue_handler.format(msg)
                self.table.insert(msg)
            else:
                time.sleep(0.1)
        if not self.__log_queue.empty():
            self.__logger.warning('El queue con la informacion de log aun no esta vacio, en seguida se vasiara.')
        while not self.__log_queue.empty():
            msg = self.__log_queue.get()
            msg = self.queue_handler.format(msg)
            try:
                self.table.insert(msg)
            except sqlite3.OperationalError:
                self.stop()
        self.__logger.info('El proceso monitor de log termino correctamente.')

    def stop(self):
        self.__stop.set()

    @property
    def format(self):
        if not self.__format:
            return logging.Formatter('%(asctime)s -.- %(levelname)s -.- %(message)s')
        else:
            return self.__format

    @format.setter
    def format(self, f):
        try:
            self.__format = logging.Formatter(f)
            self.queue_handler.setFormatter(self.format)
        except Exception as details:
            self.__logger.warning(f'Error al asignar el formato. Detalles: {details}')

    def __del__(self):
        self.__logger.info(f'Deteniendo el proceso {self.__logger.name} para {self.logger.name}')
        self.stop()

    def __enter__(self):
        self.__logger.info('Iniciando el proceso {self.__logger.name} para {self.logger.name}')
        logging.basicConfig(level=logging.DEBUG)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


class ConnectionSQLite:
    def __init__(self, name_database):
        self.__logger = logging.getLogger('ConnectionSQLite')
        self.__connection = None
        self.__name_database = name_database

    @property
    def connection(self):
        try:
            if self.__connection:
                try:
                    self.__connection.commit()
                except sqlite3.ProgrammingError:
                    self.__connection = sqlite3.connect(self.__name_database)
            else:
                self.__connection = sqlite3.connect(self.__name_database)
        except sqlite3.Error as e:
            self.__logger.error(e)
            self.__connection = None
        return self.__connection


class Table(ConnectionSQLite):
    def __init__(self, datanase, name, campos=None):
        super().__init__(datanase)
        self.name = name.replace(' ', '_')
        self.__logger = logging.getLogger('Table')
        self.__database = datanase
        self.__campos = campos
        self.make_table()

    @property
    def campos(self):
        if self.__campos:
            return str(', ').join([f'{campo}' for campo in self.__campos])
        else:
            raise KeyError

    @campos.setter
    def campos(self, value):
        self.__campos = value

    @property
    def campo_type(self):
        return str(', ').join([f'{campo} {self.__campos[campo]}' for campo in self.__campos])

    def make_table(self):
        sql_create_table = f""" CREATE TABLE IF NOT EXISTS {self.name} (
                                            id integer PRIMARY KEY,
                                            {self.campo_type}
                                        ); """
        if self.connection is not None:
            with self.connection as conn:
                try:
                    cur = conn.cursor()
                    cur.execute(sql_create_table)
                except sqlite3.Error as e:
                    self.__logger.error(e)
        else:
            self.__logger.error("Error! cannot create the database connection.")

    def values(self):
        return str(', ').join(['?' for e in range(len(self.__campos))])

    def insert(self, regustro):
        sql = f''' INSERT INTO {self.name} ({self.campos})
                          VALUES({self.values()}) '''
        with self.connection as conn:
            try:
                cur = conn.cursor()
                cur.execute(sql, tuple(regustro.split(' -.- ')))
            except Exception as details:
                print(details)
            except sqlite3.OperationalError as detalles:
                print(f'La conexion esta bloqueada Detalles: {detalles}')
            else:
                return cur.lastrowid


def test(logger, base_name):
    dl = DaemonLogger(logger, base_name)
    with dl:
        logger.debug('Chale')
        logger.warning('Con la charola')


def consultar_si_funciona(database, table_name):
    sql = f'''SELECT * FROM {table_name} WHERE level LIKE 'WARNING' '''
    conn = sqlite3.connect(f'{database}.db')
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    print(f'resultado de la consulta: {rows}')


if __name__ == '__main__':
    base_name_t = 'Testeando_ando'
    my_table_name = 'Nuevo_logger'
    _logger = logging.getLogger(my_table_name)
    test(_logger, base_name_t)
    time.sleep(2)
    consultar_si_funciona(base_name_t, my_table_name)
