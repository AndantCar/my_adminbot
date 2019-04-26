#!/usr/bin/python3
# -*- encoding:utf-8 -*-

import os
import sqlite3
from sqlite3 import Error
from datetime import datetime


name_database = os.path.join(os.getcwd(), os.path.join('database', 'base_payments.db'))


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
        print(e)

    return None


def create_table(conn, create_table_sql):
    """ create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)


def make_database_and_tables():
    database = os.path.join(os.getcwd(), name_database)

    sql_create_users_table = """ CREATE TABLE IF NOT EXISTS users (
                                        id integer PRIMARY KEY,
                                        name text NOT NULL,
                                        chat_id text
                                    ); """

    sql_create_payments_table = """CREATE TABLE IF NOT EXISTS payments (
                                    id integer PRIMARY KEY,
                                    name text NOT NULL,
                                    chat_id integer NOT NULL,
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
    # create a database connection
    conn = create_connection(database)
    if conn is not None:
        with conn:
            create_table(conn, sql_create_users_table)
            create_table(conn, sql_create_payments_table)
            create_table(conn, sql_create_messages_ids_table)
    else:
        print("Error! cannot create the database connection.")


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


def delete_all_message_id_db(conn, chat_id):
    """

    :param conn:
    :param chat_id:
    :return:
    """
    sql = f'''DELETE FROM messages_ids WHERE chat_id=? '''
    cur = conn.cursor()
    cur.execute(sql, (chat_id,))


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
    #chat_ids = [chat_id[0] for chat_id in rows]
    return rows
    #return chat_ids


if __name__ == '__main__':
    if not os.path.exists(os.path.join(os.getcwd(), name_database)):
        make_database_and_tables()
    # main()
    # create_user(create_connection(name_database), ('carlos', '1234'))
    # save_message_id(create_connection(name_database), '123454321', '1234')
    # print(get_all_message_id(create_connection(name_database), '1234'))
    # create_payment(create_connection(name_database), 'renta', 1234)
    # print(payments_list(create_connection(name_database), '1234'))
    # print(get_all_users(create_connection(name_database)))
    # print(get_user(create_connection(name_database), '1231'))
    get_status_payment(create_connection(name_database), 'renta', 547815968)
