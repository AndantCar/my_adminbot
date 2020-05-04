import logging
import os
import traceback

import tools_sqlite
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, ConversationHandler, CallbackQueryHandler, MessageHandler, Filters

from telegram_tools_bot import telegram_tools

LOGGER = logging.getLogger('Bot')
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

TOKEN = '635048049:AAHmD4MK8AgiiMEzp8ZntRl5EfbQRa7aMVg'

(REGISTRO, INITIAL_MENU, PAYMENTS_LIST, NEW_PAYMENT, SHOW_LIST, BACK_TO_LIST,
 CANCEL_NEW, INPUT_NAME, SELECT_LIST, DELETE_ELEMENT, EDIT_ELEMENT,
 BACK_TO_SHOW_LIST, EDIT_NAME, EDIT_AMOUNT, EDIT_RECURRENCE) = map(chr, range(15))

SELECTING_ACTION, PAYMENT_LIST, PAYMENT_STATE, SAVE_INPUT, MENU_PAYMENT = map(chr, range(15, 20))
END = ConversationHandler.END


def __message(text, update, buttons):
    keyboard = InlineKeyboardMarkup(buttons)
    update.message.reply_text(text=text, reply_markup=keyboard)


def __message_query(text, update, buttons):
    keyboard = InlineKeyboardMarkup(buttons)
    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=keyboard)


def start(update, context):
    # text = '''Hola soy un admin'''
    # buttons = [[InlineKeyboardButton(text="Lista de gastos", callback_data=str(PAYMENT_LIST))]]
    # keyboard = InlineKeyboardMarkup(buttons)
    # if context.user_data.get(START_OVER):
    #     update.callback_query.answer()
    #     LOGGER.info(update.callback_query.answer())
    #     update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    # else:
    #     update.message.reply_text(
    #         'Hola, soy AdminBot y aqui podras guardar toda la informacion que quieras administrar')
    #     update.message.reply_text(text=text, reply_markup=keyboard)
    # context.user_data[START_OVER] = False
    # return SELECTING_ACTION
    print('In start')
    if not tools_sqlite.user_exist(tools_sqlite.create_connection(tools_sqlite.name_database),
                                   update.message.chat.id):
        print('In if start')
        if not context.user_data.get('START_OVER'):
            text = '''Hola veo que una no has iniciado sesion.'''
            buttons = [[InlineKeyboardButton(text="REGISTRARSE", callback_data=str(REGISTRO))],
                       [InlineKeyboardButton(text='INICIAR SESION', callback_data=str(INITIAL_MENU))]]
            __message(text, update, buttons)
            return SELECTING_ACTION
    else:
        print('In else start')
        return initial_menu(update, context)


def initial_menu(update, context):
    text = 'Menu inicial.'
    buttons = [[InlineKeyboardButton(text='Lista de pagos', callback_data=str(PAYMENT_LIST))]]
    if update.callback_query:
        __message_query(text, update, buttons)
    else:
        __message(text, update, buttons)
    return SELECTING_ACTION


def registrarse(update, context):
    try:
        tools_sqlite.create_user(tools_sqlite.create_connection(tools_sqlite.name_database),
                                 (telegram_tools.get_name(update.callback_query.message),
                                  update.callback_query.message.chat.id))
    except Exception as details:
        LOGGER.warning(f'Error: {details}')
        LOGGER.warning(traceback.format_exc())
    else:
        return initial_menu(update, context)
    return SELECTING_ACTION


def __payment_list_menu(update, context):
    text = 'Aqui podras administrar tu lista de pagos'
    buttons = [[InlineKeyboardButton(text='Nuevo', callback_data=str(NEW_PAYMENT)),
                InlineKeyboardButton(text='Mostrar lista', callback_data=str(SHOW_LIST))],
               [InlineKeyboardButton(text='Atras', callback_data=str(END))]]
    if update.callback_query:
        __message_query(text, update, buttons)
    else:
        __message(text, update, buttons)
    return PAYMENT_LIST


def add_payment(update, context):
    text = '''Nuevo'''
    buttons = [
        [
            InlineKeyboardButton(text='Añadir', callback_data=str(INPUT_NAME))
        ],
        [
            InlineKeyboardButton(text='Cancelar', callback_data=str(CANCEL_NEW))
        ]
    ]
    keyboard = InlineKeyboardMarkup(buttons)
    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    return PAYMENT_STATE


def get_input(update, context):
    text = 'Okay, escriba el nuevo pago.'

    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text)
    return SAVE_INPUT


def save_input(update, context):
    tools_sqlite.create_payment(tools_sqlite.create_connection(tools_sqlite.name_database),
                                update.message.text,
                                update.message.chat.id)
    return __payment_list_menu(update, context)


def show_list(update, context):
    names_payments = tools_sqlite.payments_list(tools_sqlite.create_connection(tools_sqlite.name_database),
                                                update.callback_query.message.chat.id)
    buttons = []
    for payment in names_payments:
        buttons.append([InlineKeyboardButton(payment, callback_data=payment.replace(' ', ''))])

    return PAYMENT_LIST


def error(update, context):
    """Log Errors caused by Updates."""
    LOGGER.warning('Update "%s" caused error "%s"', update, context.error)


def __format_pattern(key):
    return f'^{key}$'


def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # second_level_conv_handler = ConversationHandler(
    #     entry_points=[CallbackQueryHandler(__payment_list_menu,
    #                                        pattern='^' + PAYMENT_LIST + '$')],
    #     states={SHOWING: [CallbackQueryHandler(add_payment,
    #                                            pattern='^' + str(ADD_PAYMENT) + '$')],
    #             SELECTING_ACTION: [CallbackQueryHandler(start,
    #                                                     pattern='^' + str(END) + '$')]},
    #     fallbacks=[]
    # )

    conv_handler = ConversationHandler(entry_points=[CommandHandler('start', start)],
                                       states={
                                           SELECTING_ACTION: [
                                               CallbackQueryHandler(registrarse,
                                                                    pattern=__format_pattern(REGISTRO)),
                                               CallbackQueryHandler(initial_menu,
                                                                    pattern=__format_pattern(INITIAL_MENU)),
                                               CallbackQueryHandler(__payment_list_menu,
                                                                    pattern=__format_pattern(PAYMENT_LIST))
                                           ],
                                           PAYMENT_LIST: [
                                               CallbackQueryHandler(add_payment,
                                                                    pattern=__format_pattern(NEW_PAYMENT)),
                                               CallbackQueryHandler(show_list,
                                                                    pattern=__format_pattern(SHOW_LIST)),
                                               CallbackQueryHandler(initial_menu,
                                                                    pattern=__format_pattern(END))

                                           ],
                                           PAYMENT_STATE: [
                                               CallbackQueryHandler(get_input,
                                                                    pattern=__format_pattern(INPUT_NAME)),
                                               CallbackQueryHandler(__payment_list_menu,
                                                                    pattern=__format_pattern(CANCEL_NEW))
                                           ],
                                           SAVE_INPUT: [
                                               MessageHandler(Filters.text, save_input)
                                           ],
                                           MENU_PAYMENT: [

                                           ]

                                       },
                                       fallbacks=[])

    dp.add_handler(conv_handler)
    dp.add_error_handler(error)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    try:
        if not os.path.exists(tools_sqlite.name_database):
            tools_sqlite.make_database_and_tables()
        main()
    except Exception:
        print('Me rompi aqui')
