#!/usr/bin/python3
# -*- encoding:utf-8 -*-

import datetime
import os
import json
import pickle
import logging

from copy import deepcopy

import requests

from telebot import types
from .tools_sqlite import save_message_id, create_connection, get_all_message_id, delete_all_message_id_db


__author__ = 'Carlos Añorve'
__version__ = '1.0'

__all__ = ['get_chat_id_and_message_id',
           'get_name',
           'make_buttons_of_dict',
           'make_button_of_list',
           'add_next_prev_buttons',
           'read_json',
           'dataframe2json',
           'json2str',
           'request_is_ok',
           'response2dict',
           'send_message',
           'send_message_from_bot']

logger = logging.getLogger('Tools bot')
level_debug = '1'
levels = {'1': logging.DEBUG,
          '2': logging.INFO,
          '3': logging.WARNING,
          '4': logging.ERROR,
          '5': logging.CRITICAL}

#logging.basicConfig(level=levels[level_debug],
#                    format='%(asctime)s - %(name)s - %(message)s')

TOKEN = '635048049:AAHmD4MK8AgiiMEzp8ZntRl5EfbQRa7aMVg'
URL_API = 'https://api.telegram.org/bot{0}/{1}'


def save_with_pickle(obj, name, path=None):
    """
    Guarda un archivo en la ruta especificada..

    Args:
        obj(Any): Cualqier objeto de python.
        name(str):
        path(str):

    Returns:
        None
    """
    if path is None:
        path = os.path.realpath(__file__)
        path = os.path.split(path)[0]
    else:
        if os.path.exists(path):
            try:
                os.mkdir(path)
            except (FileNotFoundError, Exception):
                try:
                    os.makedirs(path)
                except (FileNotFoundError, Exception):
                    logger.warning('No fue posible crear la ruta para guardar el archivo.'
                                   'Se guardara en la ruta donde se ejecuta el rograma.')
                    path = os.path.realpath(__file__)
                    path = os.path.split(path)[0]
    with open(os.path.join(path, name), 'wb') as obj_file:
        pickle.dump(obj, obj_file)


def get_date_from_message(message):
    """
    Extrae la fecha del mensaje.

    Args:
        message(telebot.types.Message, telebot.types.CallbackQuery): Mensaje recibido por un bot del modulo Telebot

    Returns:
         Fecha(time.localtime): fecha del mensaje.
    """
    date = None
    try:
        date = message.date
    except AttributeError:
        try:
            date = message.message.date
        except AttributeError:
            logger.warning('No es posible obtener fecha del mensaje.')
    return date


def open_with_picke(name, path=None):
    """
    Abre un archivo guardado con pickle.

    Args:
        name(str): Nombre del archivo.
        path(str): Ruta donde se encientra el archivo en caso de ser
            None se buscara el archivo en la ruta donde se
            ejecuta el programa.

    Returns:
         Any
    """
    try:
        if path is None:
            path = os.path.realpath(__file__)
            path = os.path.split(path)[0]
            path = os.path.join(path, name)
        else:
            if not os.path.isdir(path):
                logger.warning('El path espesificado no es un directorio.')
                return None
            else:
                path = os.path.join(path, name)
        with open(path, 'rb') as pf:
            data = pickle.load(pf)
    except Exception as details:
        logger.warning('Error insesperado en funcion "open_with_pickle"\n'
                       'Detalles: {}'.format(details))
    else:
        return data


def get_chat_id_and_message_id(message, save_in_database=False, name_database=''):
    """
    Obtiene el id del chat con usuario y el mensage.

    Args:
        message(telebot.types.Message, telebot.types.CallbackQuery): Mensaje recibido por el bot.
        save_in_database(bool):
        name_database(str):

    Returns:
        chat_id, message_id(int, str): idntificador del char e identificador del mensaje recibido.
    """
    try:
        logger.debug('Intentando obtener el id del chat.')
        chat_id = message.from_user.id
    except AttributeError:
        logger.error('Errro al extraer el id del chat')
        return None
    try:
        logger.debug('Intentando obtener el id del mensage')
        message_id = message.message.message_id
    except AttributeError:
        logger.error('Error al intentar obtener el id del mensage')
        try:
            message_id = message.message_id
        except AttributeError:
            logger.error('Error al intentar pasar a int el id del mensaje.')
            return None
    # fecha = datetime.datetime.fromtimestamp(get_date_from_message(message))
    # retraso = datetime.datetime.today() - fecha
    # if int(retraso.total_seconds()) > 40:
    #     print(f'se reciobio un mensaje demaciado retrasado.retraso de {retraso} segundos\n'
    #           f'Hora de recepcion: {fecha}')
    #     return None
    if save_in_database:
        save_message_id(create_connection(name_database), message_id, chat_id)
    return chat_id, message_id


def get_name(message):
    """
    Extrae el nombre del usuario que envio en mensaje.

    Args:
        message(telebot.types.Message): Mensaje recibido por el bot.

    Returns:
         name(str): Nombre del usuario que mando el mensaje.
    """
    try:
        name = message.from_user.first_name
    except AttributeError:
        logger.warning('No es posible obtener el nombre del usuario.')
        return None
    else:
        if name is None:
            logger.warning('El nombre de usuario apaece vacio.')
            name = ''
    try:
        last_name = message.from_user.last_name
    except AttributeError:
        logger.error('No es posible obtener el ultimo nombre del usuario.')
    else:
        if last_name is None:
            logger.info('El ultimo nombre del usuario aparece vacio.')
        else:
            name += ' {}'.format(last_name)
    return name


def make_buttons_of_dict(estructure, rows=3):
    """
    Crea un KeyBoardMarkup con la estructura pasada

    Args:
        estructure(dict): Estructura que con la que se creara el markup
        rows(int): Determin la cntidade de columas para mostra botones.

    Returns:
         KeyBoardMarkup
    """
    try:
        keyboard_markup = types.InlineKeyboardMarkup()
    except Exception as details:
        logger.warning('Error al intentar crear el keryboardMarkup\n'
                       'Details: {}'.format(details))
        return None
    buttons = []
    for button in estructure:
        try:
            keyboard_button = types.InlineKeyboardButton(button, callback_data=estructure[button])
        except Exception as details:
            logger.error('No fue posible crear el boton {}\n'
                         'Details: {}'.format(button, details))
        else:
            buttons.append(deepcopy(keyboard_button))
            del keyboard_button
            if len(buttons) == rows:
                keyboard_markup.row(*buttons)
                buttons = []
    if len(buttons) > 0:
        keyboard_markup.row(*buttons)
    return keyboard_markup


def read_json(path):
    """
    Lee un archivo json y lo pasa a diccionario.

    Args:
        path(str): ubicacion del archivo en sistema.

    Returns:
         Devuelve un diccionario con la estructura del json leido.
    """
    try:
        with open(path, 'r') as json_file:
            json_data = json.loads(json_file.read())
    except Exception as details:
        logger.warning('Error al intentar leer el archivo json.\n'
                       'Path: {}\n'
                       'Detalles: {}'.format(path, details))
    else:
        return json_data


def make_many_markups_from_list(names_buttons, rows=3, columns_markup=3):
    """

    :param names_buttons(list):
    :param rows:
    :param columns_markup:
    :return:
    """
    markups = {}
    names_buttons.sort()
    all_buton_by_markup = rows * columns_markup
    if len(names_buttons) > all_buton_by_markup:
        index_markup = 1
        list_to_markup = []
        for name_button in names_buttons:
            if len(list_to_markup) < all_buton_by_markup:
                list_to_markup.append(name_button)
            else:
                markups[index_markup] = add_next_prev_buttons(make_button_of_list(list_to_markup, rows=rows))
                list_to_markup = []
                index_markup += 1
        if len(list_to_markup) != 0:
            markups[index_markup] = add_next_prev_buttons(make_button_of_list(list_to_markup, rows=rows))
    return markups


def add_next_prev_buttons(markup):
    """
    Añade botones de anterior y siguiente a un markup

    Args:
        markup(types.InlineKeyboardMarkup):

    Returns:

    """
    next_button = types.InlineKeyboardButton(text='Siguiente',
                                             callback_data='Siguiente')
    prev_button = types.InlineKeyboardButton(text='Anterior',
                                             callback_data='Anterior')

    markup.row(prev_button, next_button)
    return markup


def add_button_cancel(markup, estructure=None):
    """
    Añade un boton de cancelar a un markup

    Args:
        markup(types.InlineKeyboardMarkup):
        estructure(dict):

    Returns:
        types.InlineKeyboardMarkup
    """
    if estructure is None:
        cancel_button = types.InlineKeyboardButton(text='Cancelar',
                                                   callback_data='Cancelar')
    else:
        name = list(estructure)[0]
        calback_data = list(estructure.values())[0]
        cancel_button = types.InlineKeyboardButton(text=name,
                                                   callback_data=calback_data)
    markup.row(cancel_button)
    return markup


def make_button_of_list(names_buttons, rows=3, commands=False, callback=False, add_back_button=False):
    """
    Crea una estructura de botones a partir de una lista
    Solo se podra mostra un maximo de 100 botones en pantalla, para
    usar mas botones use mas de 1 markup.

    Args:
        names_buttons(list): lista de nombre de botones.
        rows(int): Define la cantidad de columnas en el layout de botones
        commands(bool): Define si los botones creados seran comandos.
        callback(bool): Define si los botones se usaran para un callback_query_handler
        add_back_button(bool):

    Returns:
        keyboard_markup(types.InlineKeyboardMarkup): Markup con los botones.
    """
    butons = []
    try:
        keyboard_markup = types.InlineKeyboardMarkup()
    except Exception as details:
        logger.warning('Error al intentar crear el keyboardMarkup\n'
                       'Detalles: {}'.format(details))
        return None
    for name_button in names_buttons:
        try:
            if commands and not callback:
                inline_button = types.InlineKeyboardButton(name_button,
                                                           callback_data='/{}'.format(name_button))
            elif callback and not commands:
                inline_button = types.InlineKeyboardButton(name_button,
                                                           callback_data='cb_{}'.format(name_button))

            elif not callback and not commands:
                inline_button = types.InlineKeyboardButton(name_button,
                                                           callback_data=name_button)
            else:
                logger.warning('No debe pasar los argumentos callback y commands como True al mismo tiempo.')
                raise ArgumentError('Conflicto entre argumentos.')
        except Exception as details:
            logger.warning('Error al intentar crear el boton.\n'
                           'Details: {}'.format(details))
        else:
            butons.append(deepcopy(inline_button))
            del inline_button
            if len(butons) == rows:
                keyboard_markup.row(*butons)
                butons = []
    if len(butons) > 0:
        keyboard_markup.row(*butons)
    if add_back_button:
        keyboard_markup.row(types.InlineKeyboardButton('Ir a inicio', callback_data='go_start'))
    return keyboard_markup


def delete_message(token, chat_id, message_id):
    params = {'chat_id': str(chat_id), 'message_id': message_id}
    try:
        response = requests.get(url=URL_API.format(token, 'deleteMessage'), params=params)
    except Exception as details:
        logger.warning('Error al intentar enviar el mensaje.\n'
                       'Details: {}'.format(details))
    else:
        try:
            request_is_ok(response)
        except Exception as details:
            pass


def delete_all_message(token, chat_id, name_database):
    """

    :param token:
    :param chat_id:
    :param name_database:
    :return:
    """
    message_ids = get_all_message_id(create_connection(name_database), chat_id)
    for message_id in message_ids:
        delete_message(token, chat_id, message_id)



def dataframe2json(data_frame):
    """
    Convierte el data frame obtenido del
    indicador y lo convierte a json.

    Nota:
    El data frame debe mantener el nombre del simbolo
    en la primera columan despues del indice

    Args:
        data_frame(): Dataframe btenido del indicador

    Returns:
        Devuelve los datos del data frame en un json.
    """
    llaves = ['SYMBOL', 'open_time_dt', 'close', 'MONEY_FLOW_INDEX', 'MACDT_HIST',
              'volume', 'VMA(10)', 'SIGNAL']
    senales = {}
    for datos in data_frame.values:
        senal = {}
        for i in range(len(llaves)):
            try:
                senal[llaves[i + 1]] = str(datos[i + 1])
            except IndexError:
                break
        senales[datos[0]] = senal
    return json.dumps(senales)


def json2str(json_data):
    """
    Convierte el json en un string para enviar el mensaje

    Args:
        json_data(dict): Informacion del json

    Returns:
         str_json(str): string con la informacion del json.
    """
    str_json = str()
    for llave in json_data:
        str_json += '{}:'.format(llave)
        if isinstance(json_data[llave], dict):
            str_json += '\n'
            for llave_interna in json_data[llave]:
                str_json += '  {}: '.format(llave_interna)
                str_json += json_data[llave][llave_interna]
                str_json += '\n'
        else:
            str_json += json_data[llave]
            str_json += '\n'
        str_json += '\n'
    return str_json


def request_is_ok(response):
    """
    Verifica que la espuesta de la solicitud sea satisfactoria.

    Argss:
        response(requests.models.Response): Respuesta obtenida de la solicitud.

    Returns:
        None
    """
    if response.status_code == requests.codes.ok:
        logger.debug('La solisutd se ejecuto correctamente.')
        return True
    else:
        logger.warning('Algun error ocurrio en la solicitud.\n'
                       'Error: {}'.format(response.status_code))
        raise MethodRequestError('Codigo de error: {}'.format(response.status_code))


def response2dict(response):
    """
    Convierte la respuesta obtenida a un diccionario.

    Args:
        response(requests.models.Response): Respuesta obtenida de la solicitud.
    Returns:
         dict
    """
    try:
        result = json.loads(response.text)
    except Exception as details:
        logger.error('Error al intentar obtener el json\n'
                     'se intentara con request.get.content\n'
                     'Detalles de error: {}'.format(details))
        try:
            result = json.loads(response.content)
        except Exception as details:
            logger.warning('Imposible coseguir el contenido de la solicutud\n'
                           'Detalles de error: {}'.format(details))
            raise ErrorToExtractJson(details)
    return result


def send_message(chat_id, message, token, parse_mode='HTML'):
    """
    Envia un mensaje al chat espesificado a travez de la api de telegram bot

    Args:
        chat_id(int, str): id que identifica al chat.
        message(str): Mensaje ue se quiere enviar.
        token(str): token espesifico del bot que se quiere utilizar
        parse_mode(str): Tipo de parser que se utilizara para enviar el mensaje.

    Returns:
         None
    """
    params = {'chat_id': str(chat_id), 'text': message, 'parse_mode': parse_mode}
    try:
        response = requests.get(url=URL_API.format(token, 'sendMessage'), params=params)
    except Exception as details:
        logger.warning('Error al intentar enviar el mensaje.\n'
                       'Details: {}'.format(details))
        raise MethodRequestError(details)
    else:
        request_is_ok(response)
    result = response2dict(response)
    return result


def send_message_from_bot(bot, chat_id, message_id, message, markup=None, parse_mode='HTML'):
    """
    Envia in mensage usando una instancia de un bot de telegram.

    Args:
        bot(telebot.TeleBot): Instancia de un bot de telegram.
        chat_id(int): Identificador del chat al caul se le enviara el mensaje
        message_id(int): identificador del mensaje anterior de ser posible se sobreescribira.
        message(str): Mensaje que se enviara.
        markup(types.InlineKeyboardMarkup): Un markup con los botones que se enviaran en conjunto al mensaje.
        parse_mode(str): Tipo de parser que se utilizara para enviar el mensaje.

    Returns:
        None
    """
    try:
        bot.edit_message_text(chat_id=chat_id, text=message,
                              reply_markup=markup,
                              parse_mode=parse_mode,
                              message_id=message_id)
    except Exception as details:
        logger.info(f'Detalles: {details}')
        try:
            send_only_markup(bot, chat_id, message_id, markup)
        except Exception as details:
            logging.info(details)
            bot.send_message(chat_id, message,
                             reply_markup=markup,
                             parse_mode=parse_mode)


def send_only_markup(bot, chat_id, message_id, markup=None):
    bot.edit_message_reply_markup(chat_id, message_id, reply_markup=markup)


def get_me(token):
    """
    Un método simple para probar el token de autenticación de tu bot.
    No requiere parámetros Devuelve información básica sobre el bot en
    forma de un objeto Usuario.

    Args:
        token(str): token espesifico del bot que se quiere utilizar.

    Returns:
        responce(dict): resuesta obtenida del request.
    """
    try:
        response = requests.get(URL_API.format(token))
    except Exception as details:
        logger.warning('Error al intentar hacer la solicitud de getMe\n'
                       'Detalles: {}'.format(details))
        raise MethodRequestError(details)
    else:
        request_is_ok(response)
    result = response2dict(response)
    return result


class Button:
    def __init__(self, name_button: str):
        self.command = name_button
        self.markup = make_button_of_list([name_button])


class MethodRequestError(Exception):
    def __init__(self, message):
        super(Exception, self).__init__(message)


class ArgumentError(Exception):
    def __init__(self, message):
        super(Exception, self).__init__(message)


class ErrorToExtractJson(Exception):
    def __init__(self, message):
        super(Exception, self).__init__(message)
