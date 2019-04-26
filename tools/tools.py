#!/usr/bin/python3
# -*- encoding:utf-8 -*-

import time
import json
import logging

from copy import deepcopy

import requests

from telebot import types


__author__ = 'Carlos Añorve'
__version__ = '1.0'

__all__ = ['get_message_id_and_chat_id',
           'make_buttons_of_dict',
           'make_button_of_list',
           'read_json',
           'dataframe2json']


logger = logging.getLogger(__name__)
level_debug = '1'
levels = {'1': logging.DEBUG,
          '2': logging.INFO,
          '3': logging.WARNING,
          '4': logging.ERROR,
          '5': logging.CRITICAL}

logging.basicConfig(filename=f'log_Supervisor{time.strftime("%d-%m-%Y")}.log',
                    level=levels[level_debug],
                    format='%(asctime)s - %(name)s - %(message)s')

URL_API = 'https://api.telegram.org/bot{0}/{1}'


def get_message_id_and_chat_id(message):
    """
    Obtiene el id del chat con usuario y el mensage.

    Args:
        message(telebot.types.Message, telebot.types.CallbackQuery): Mensaje recibido por el bot.

    Returns:
        chat_id, message_id(int, str): idntificador del char e identificador del mensaje recibido.
    """
    try:
        logger.debug('Intentando obtener el id del chat.')
        try:
            chat_id = int(message.from_user.id)
        except ValueError:
            print('Error al intentar pasar a int el id del chat.\n'
                  'chat_id: {}'.format(message.from_user.id))
            return None
    except AttributeError:
        logger.error('No fue posible obtener el id del chat con message.from_user.id')
        return None

    try:
        logger.debug('Intentando obtener el id del mensage')
        try:
            message_id = int(message.message_id)
        except ValueError:
            print('Error al intentar pasar a int el id del mensaje.')
            return None
    except AttributeError:
        logger.error('Error al intentar obtener el id del mensage')
        return None
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
    buttons = list()
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
                buttons = list()
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


def make_button_of_list(names_buttons, rows=3, commands=False, callback=False):
    """
    Crea una estructura de botones a partir de una lista.

    Args:
        names_buttons(list): lista de nombre de botones.
        rows(int): Define la cantidad de columnas en el layout de botones
        commands(bool): Define si los botones creados seran comandos.
        callback(bool): Define si los botones se usaran para un callback_query_handler

    Returns:
        keyboard_markup(types.InlineKeyboardMarkup): Markup con los botones.
    """
    butons = list()
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
                butons = list()
    if len(butons) > 0:
        keyboard_markup.row(*butons)
    return keyboard_markup


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


def send_message(chat_id, message, token):
    """
    Envia un mensaje al chat espesificado a travez de la api de telegram bot

    Args:
        chat_id(int, str): id que identifica al chat.
        message(str): Mensaje ue se quiere enviar.
        token(str): token espesifico del bot que se quiere utilizar

    Returns:
         None
    """
    params = {'chat_id': str(chat_id), 'text': message}
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
        logger.info(details)
        bot.send_message(chat_id, message,
                         reply_markup=markup,
                         parse_mode=parse_mode)


class MethodRequestError(Exception):
    def __init__(self, message):
        super(Exception, self).__init__(message)


class ArgumentError(Exception):
    def __init__(self, message):
        super(Exception, self).__init__(message)


class ErrorToExtractJson(Exception):
    def __init__(self, message):
        super(Exception, self).__init__(message)

