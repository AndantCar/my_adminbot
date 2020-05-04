#!/usr/bin/python3
# -*- encoding:utf-8 -*-

import logging
import os
import re
import sqlite3
import traceback
from datetime import datetime
from sqlite3 import Error

LOGGER = logging.getLogger('DatabaseTools')
BASE_PATH = os.path.join(os.getcwd(), 'database')
if not os.path.exists(BASE_PATH):
    os.mkdir(BASE_PATH)
name_database = os.path.join(BASE_PATH, 'base_payments.db')

LOGGER.debug(f'Path database: {name_database}')


def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        LOGGER.error(e)
        LOGGER.error(traceback.format_exc())
        return None


def create_table(conn, create_table_sql):
    """ create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    try:
        LOGGER.debug(f'Create table with query {create_table_sql}')
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        LOGGER.error(f'Details: {e}')
        LOGGER.error(traceback.format_exc())
        LOGGER.info(create_table_sql)


def make_database_and_tables():
    sql_create_users_table = """ CREATE TABLE IF NOT EXISTS users (
                                        id integer PRIMARY KEY,
                                        name text NOT NULL,
                                        chat_id text
                                    ); """

    sql_create_payments_table = """CREATE TABLE IF NOT EXISTS payments (
                                    id integer PRIMARY KEY,
                                    name text NOT NULL,
                                    chat_id text NOT NULL,
                                    priority integer,
                                    status_id integer,
                                    begin_date text,
                                    end_date text,
                                    FOREIGN KEY (chat_id) REFERENCES users (chat_id)
                                );"""
    sql_create_messages_ids_table = '''CREATE TABLE IF NOT EXISTS messages_ids (
                                        id integer PRIMARY KEY,
                                        message_id integer NOT NULL,
                                        chat_id integer NOT NULL)'''
    sql_create_status__table = '''CREATE TABLE IF NOT EXISTS status (
                                        id integer PRIMARY KEY,
                                        name integer NOT NULL);'''
    # create a database connection
    conn = create_connection(name_database)
    if conn is not None:
        with conn:
            create_table(conn, sql_create_users_table)
            create_table(conn, sql_create_payments_table)
            create_table(conn, sql_create_messages_ids_table)
            create_table(conn, sql_create_status__table)
    else:
        LOGGER.error("cannot create the database connection.")


def create_user(conn, user_data):
    """
    Create a new project into the projects table
    :param conn:
    :param user_data:
    :return: project id
    """
    sql = ''' INSERT INTO users(name,chat_id)
              VALUES(?,?) '''
    with conn:
        cur = conn.cursor()
        cur.execute(sql, user_data)
        return cur.lastrowid


def create_payment(conn, name, chat_id,
                   priority=None, status_id=0,
                   begin_date=None, end_date=None):
    """
    Create a new payment
    :param conn:
    :param name:
    :param chat_id:
    :param priority:
    :param status_id:
    :param begin_date:
    :param end_date:
    :return:
    """
    names_in_base = payments_list(conn, chat_id)
    if not (name in names_in_base):
        payment = (name, chat_id, priority, status_id, begin_date, end_date)
        sql = ''' INSERT INTO payments(name,chat_id,priority,status_id,begin_date,end_date)
                  VALUES(?,?,?,?,?,?) '''
        with conn:
            cur = conn.cursor()
            cur.execute(sql, payment)
            return cur.lastrowid


def main():
    database = os.path.join(os.getcwd(), name_database)

    # create a database connection
    conn = create_connection(database)
    with conn:
        # create a new project
        project = ('Carlos', '65432')
        user_id = create_user(conn, project)

        # tasks
        task_1 = ('Renta', 1, 1, user_id,
                  f'{datetime.today().date()}',
                  f'{datetime.today().date()}')
        task_2 = ('Padres', 1, 1, user_id,
                  f'{datetime.today().date()}',
                  f'{datetime.today().date()}')

        # create tasks
        create_payment(conn, *task_1)
        create_payment(conn, *task_2)


def user_exist(conn, chat_id):
    """
    CHeck if exist the user in the database
    :param conn:
    :param chat_id:
    :return:
    """
    sql = f''' SELECT * FROM users WHERE chat_id = '{chat_id}' '''
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    if [r for r in rows]:
        return True
    else:
        return False


def payments_list(conn, chat_id):
    sql = f'''SELECT name FROM payments WHERE  chat_id=?'''
    cur = conn.cursor()
    cur.execute(sql, (chat_id,))
    rows = cur.fetchall()
    names = [name[0] for name in rows]
    return names


def save_message_id(conn, message_id, chat_id):
    """

    :param conn:
    :param message_id:
    :param chat_id:
    :return:
    """

    sql = f'''INSERT INTO messages_ids(message_id, chat_id) 
              VALUES(?,?)'''
    if user_exist(conn, chat_id):
        with conn:
            cur = conn.cursor()
            cur.execute(sql, (message_id, chat_id))


def get_all_message_id(conn, chat_id):
    """

    :param conn:
    :param chat_id:
    :return:
    """
    sql = f'''SELECT message_id FROM messages_ids WHERE chat_id =? '''
    cur = conn.cursor()
    cur.execute(sql, (chat_id,))
    rows = cur.fetchall()
    messages_ids = [name[0] for name in rows]
    return messages_ids


def delete_all_message_id_of_db(conn, chat_id):
    """

    :param conn:
    :param chat_id:
    :return:
    """
    sql = f'''DELETE FROM messages_ids WHERE chat_id=? '''
    with conn:
        cur = conn.cursor()
        cur.execute(sql, (chat_id,))


def delete_payment(conn, chat_id, name_payment):
    """

    :param conn:
    :param chat_id:
    :param name_payment:
    :return:
    """
    sql = f'''DELETE FROM payments WHERE chat_id=? AND name=? '''
    with conn:
        cur = conn.cursor()
        cur.execute(sql, (chat_id, name_payment))


def get_all_users(conn):
    """

    :param conn:
    :return:
    """
    sql = f'''SELECT chat_id FROM users'''
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    chat_ids = [chat_id[0] for chat_id in rows]
    return chat_ids


def get_status_payment(conn, name_payment, chat_id):
    """

    :param conn:
    :param name_payment:
    :param chat_id:
    :return:
    """
    sql = f'''SELECT * FROM payments WHERE name='{name_payment}' AND chat_id={chat_id} '''
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    return rows


def add_date_of_payment(conn, chat_id, str_fecha, name):
    """

    Args:
        conn:
        chat_id:
        str_fecha(str):

    Returns:

    """
    re_dias = re.compile(r'[1-2][0-9]|3[0-1]|[1-9]')
    dias = re_dias.findall(str_fecha)
    dia, flag, fecha = 0, 0, None
    if len(dias) == 1:
        dia = int(dias[0])
        if str_fecha.replace(dias[0], '').lower() == 'm':
            flag = 1
    if flag and dia:
        if flag == 1:
            fecha = datetime.today().replace(day=dia)
            if fecha < datetime.today():
                fecha = fecha.replace(month=fecha.month + 1)
    if fecha:
        end_date = f'{fecha.replace(month=fecha.month + 1).date()}'
        begin_date = f'{fecha.date()}'
        params = (begin_date, end_date, chat_id, name)
        sql = ''' UPDATE payments SET begin_date=?, end_date=? WHERE chat_id=? AND name=?'''
        with conn:
            cur = conn.cursor()
            cur.execute(sql, params)
        return None
    else:
        return 'La fecha ingresada no es valida.'


def update_status(conn, chat_id):
    """
    Args:
        conn:
        chat_id:

    Returns:

    """
    sql = ''' UPDATE payments SET status_id=? WHERE chat_id=?'''
    params = (1, chat_id)
    with conn:
        cur = conn.cursor()
        cur.execute(sql, params)


def get_name(conn, chat_id):
    """

    :param conn:
    :param chat_id:
    :return:
    """
    sql = '''SELECT name FROM users'''
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    names = [chat_id[0] for chat_id in rows]
    return names[0]


def get_all_dates(conn):
    """

    :param conn:
    :return:
    """
    sql = '''SELECT begin_date, chat_id, status_id, name FROM payments'''
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    messages_ids = {}
    for name in rows:
        if not name[2]:
            if not (name[1] in messages_ids):
                messages_ids[name[0]] = []
            messages_ids[name[0]].append((name[1], name[3]))
    return messages_ids


if __name__ == '__main__':
    if not os.path.exists(name_database):
        make_database_and_tables()
