#!/usr/bin/python3
# -*- encoding:utf-8 -*-
import logging
import sqlite3


class SqliteTools:
    def __init__(self, name_database, tables_names=None):
        self.__logger = logging.getLogger(name_database)
        if tables_names is None:
            self.tables_names = {'users': {'chat_id': 'integer',
                                           'nombre': 'text',
                                           'last_name': 'text',
                                           'message': 'text'},
                                 'last_id_uodate': {'id_update': 'integer'}}
        else:
            self.tables_names = tables_names
        self.name_database = name_database
        self.tables = tables_names
        if self.tables_names:
            self.__make_table()

    def __make_connection(self):
        conn = sqlite3.connect(self.name_database)
        return conn

    def __make_table(self):
        for table in self.tables_names:
            campo = 'id integer PRIMARY KEY, '
            for c_table in self.tables_names[table]:
                campo += f'{c_table} {self.tables_names[table][c_table]}, '
            campos = f'({campo[:-2]});'
            sql = f"CREATE TABLE IF NOT EXISTS {table} {campos}"""
            conn = self.__make_connection()
            with conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute(sql)
                except sqlite3.Error as details:
                    self.__logger.error(f'Error al intentar crear las tablas {details}')

    def insert_data_users(self, datos):
        sql = f'''INSERT INTO users (chat_id, nombre, last_name, message) VALUES (?, ?, ?, ?)'''
        conn = self.__make_connection()
        with conn:
            try:
                cursor = conn.cursor()
                cursor.execute(sql, datos)
                return cursor.lastrowid
            except sqlite3.Error as details:
                self.__logger.warning(f'Error al intentar insertar la informacion {datos}. Detalles: {details}')

    def insert_data_last_id_update(self, datos):
        sql = f'''INSERT INTO last_id_uodate (id_update) VALUES ({datos})'''
        conn = self.__make_connection()
        with conn:
            try:
                cursor = conn.cursor()
                cursor.execute(sql)
                return cursor.lastrowid
            except sqlite3.Error as details:
                self.__logger.warning(f'Error al intentar insertar la informacion {datos}. Detalles: {details}')

    def insert_data(self):
        pass

    def get_last_id_update(self):
        sql = f'''SELECT MAX(id_update) FROM last_id_uodate'''
        conn = self.__make_connection()
        with conn:
            try:
                cursor = conn.cursor()
                cursor.execute(sql)
            except sqlite3.Error as details:
                self.__logger.warning(f'Error al intentar recuperar el ultimo id_update. Details: {details}')
            else:
                rows = cursor.fetchall()
        if not rows[0][0]:
            return 0
        else:
            return rows[0][0]

    def select_data(self):
        pass

    def delete_data_id_update(self):
        sql = f'''DELETE FROM last_id_uodate'''
        conn = self.__make_connection()
        with conn:
            try:
                cursor = conn.cursor()
                cursor.execute(sql)
            except sqlite3.Error as detils:
                self.__logger.info(f'Error al intentar borrar el registro. Detalles: {detils}')

    def update_data(self):
        pass
