#!/usr/bin/python3
# -*- encoding:utf-8 -*-

from telegram_tools_bot import telegram_tools

# Variables de control de flujo

# MARKUPS
MARKUP_MENU_PRINCIPAL = telegram_tools.make_button_of_list(
    ['Lista De Gastos', 'Administraar contraseñas', 'Administrador de tareas', 'Base de datos', 'Limpiar chat'])
MARKUP_REGISTRO = telegram_tools.make_button_of_list(['Registrarse'])
MARKUP_PAYMENT_CONFIGURATION = telegram_tools.make_buttons_of_dict({'Mostrar lista': 'show_list',
                                                                    'Añadir un pago': 'new_payment',
                                                                    '<<Atras': 'start',
                                                                    "Ayuda": 'help_new_payment'})
MARKUP_HOME = telegram_tools.make_buttons_of_dict({'<<Ir a inicio': 'start'})
MARKUP_HOME_AND_BACK = telegram_tools.make_buttons_of_dict({'<<Ir a inicio': 'start',
                                                            '<< Atras': 'show_list'})
MARKUP_GO_LIST_PAYMENTS = telegram_tools.make_buttons_of_dict({'<< Atras': 'show_list'})
MARKUP_PAYMENT_MENU = telegram_tools.make_buttons_of_dict({'Actualizar fecha de pago': 'add_payment_date',
                                                           'Marcar como pagado': 'do_payment',
                                                           'Eliminar de la lista': 'delete_payment',
                                                           '<< Atras': 'show_list',
                                                           'Ayuda': 'help_add_date'}, 2)
MARKUP_DEVELOP = telegram_tools.make_buttons_of_dict({'<<Ir a inicio': 'start'})

# MESSAGES
PLANTILLA = '''<b>{}</b>'''
MESSAGE_SELECCCION_DE_SIMBOLO = PLANTILLA.format('Selecciona el símbolo del cual deseas recibir notificaciones.')
MESSAGE_LISTA_DE_PAGOS = PLANTILLA.format('Aqui tienes la lista de los pagos que tienes pendientes.')
MESSAGE_ANADIR_NUEVO_PAGO = PLANTILLA.format('Ingresa el nombre del pago.')
MESSAGE_SALUDO_START = PLANTILLA.format('Hola {}')
MESSAGE_SELECCIONA_UNA_OPCION = PLANTILLA.format('Selecciona la opción que necesites.')
MESSAGE_FINALIZACION_DE_REGISTRO = PLANTILLA.format('Listo!\nAhora puedes usar este bot ')
MESSAGE_HELP_MESSAGE = PLANTILLA.format('Que puedes hacer con este bot?')
MESSAGE_SPAM_WARNING = PLANTILLA.format('Por favor evita hacer spam en el chat para mantenerlo limpio y organizado\n'
                                        'Puedes limpiar el historial o borrar los mensajes spam si así lo prefieres.')
MESSAGE_NEW_USER = PLANTILLA.format('Hola {} veo que eres nuevo usando este bot quieres empezar a usarme?')
MESSAGE_NEW_PAYMENT_NAME = PLANTILLA.format('Nombre del pago')
MESSAGE_AYUDA_NEW_PAYMENT = PLANTILLA.format('Para asignar un nuevo pago basta con enviar el nombre del pago')
MESSAGE_AYUDA_ADD_DATE = PLANTILLA.format(f'Para asignar la frecuencia con la que realizará el pago, use la sintaxis'
                                          f'"dia"m por ejemplo si el pago se realizará el dia 15 de cada mes asigne'
                                          f'15m.\nconsidere que '
                                          f'solo se puede agregar una frecuencia mensual en esta version.')
MESSAGE_STATUS_PAYMENT = PLANTILLA.format('Nombre: {}\nStatus: {}\nFecha limite: {}')
MESSAGE_ADD_DATE = PLANTILLA.format('Asigne con que frecuencia se realizará el pago')
MESSAGE_DEVELOP = PLANTILLA.format('Esta opción un esta en desarollo.')
MESSAGE_GET_DATABASE = PLANTILLA.format('Esta es la base de datos mas reciente.')

# Flags
FLAG_NEW_PAYMENT = 1
FLAG_PAYMENTS_LIST = 2
FLAG_ADD_DATE = 3
