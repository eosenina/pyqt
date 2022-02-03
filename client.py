import argparse
import sys
import json
import socket
import time
import logging
import threading
import logs.configs.client_logger_config
from common.settings import ACTION, PRESENCE, DEFAULT_IP_ADDRESS, DEFAULT_PORT, RESPONSE, ERROR, TIME, USER, \
    ACCOUNT_NAME, TYPE, STATUS, MESSAGE, MESSAGE_TEXT, SENDER, DESTINATION, EXIT
from common.messages import get_message, send_message
from common.decorators import Log

logger = logging.getLogger('client')


@Log()
def create_presence_message(user_name='Guest', user_status='I\'m here'):
    msg = {
        ACTION: PRESENCE,
        TIME: time.time(),
        TYPE: STATUS,
        USER: {
            ACCOUNT_NAME: user_name,
            STATUS: user_status
        }
    }
    logger.debug(f'{msg[ACTION]} сообщение сформировано для пользователя {user_name}')
    return msg


@Log()
def create_exit_message(user_name):
    return {
        ACTION: EXIT,
        TIME: time.time(),
        ACCOUNT_NAME: user_name
    }


@Log()
def process_answer(message):
    if RESPONSE in message:
        if message[RESPONSE] == 200:
            return '200 : OK'
        return f'400 : {message[ERROR]}'
    raise ValueError


@Log()
def create_message(sock, account_name='Guest'):
    recipient = input('Введите получателя сообщения: ')
    message_text = input('Введите текст сообщения: ')
    message_dict = {
        ACTION: MESSAGE,
        SENDER: account_name,
        DESTINATION: recipient,
        TIME: time.time(),
        MESSAGE_TEXT: message_text
    }
    logger.debug(f'Сформировано сообщение: {message_dict}')
    try:
        send_message(sock, message_dict)
        logger.info(f'Отправлено сообщение для пользователя {recipient}')
    except OSError:
        logger.critical('Потеряно соединение с сервером.')
        sys.exit(1)


@Log()
def message_from_server(sock, my_name):
    while True:
        try:
            message = get_message(sock)
            if ACTION in message and message[ACTION] == MESSAGE and SENDER in message and DESTINATION in message \
                    and MESSAGE_TEXT in message and message[DESTINATION] == my_name:
                print(f'\nПолучено сообщение от пользователя {message[SENDER]}:\n{message[MESSAGE_TEXT]}')
                logger.info(f'Получено сообщение от пользователя {message[SENDER]}:\n{message[MESSAGE_TEXT]}')
            else:
                logger.error(f'Получено некорректное сообщение с сервера: {message}')
        except (OSError, ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError):
            logger.critical(f'Потеряно соединение с сервером.')
            break


@Log()
def user_interactive(sock, user_name):
    while True:
        command = input('Введите команду: msg - отправить сообщение, q - выход: ')
        if command == 'msg':
            create_message(sock, user_name)
        elif command == 'q':
            send_message(sock, create_exit_message(user_name))
            print('Завершение соединения.')
            logger.info('Завершение работы по команде пользователя.')
            time.sleep(0.5)
            break
        else:
            print('Команда не распознана, попробойте снова.')


@Log()
def parse_arguments():
    client_parser = argparse.ArgumentParser()
    client_parser.add_argument('addr', default=DEFAULT_IP_ADDRESS, nargs='?')
    client_parser.add_argument('port', default=DEFAULT_PORT, type=int, nargs='?')
    client_parser.add_argument('-n', '--name', default=None, nargs='?')
    arguments = client_parser.parse_args(sys.argv[1:])
    server_address = arguments.addr
    port = arguments.port
    client_name = arguments.name

    if port > 65535 or port < 1024:
        logger.critical(f'Указан неверный номер порта: {port}. Допустимые номера с 1024 до 65535.')
        sys.exit(1)
    return server_address, port, client_name


@Log()
def process_message_from_server(message):
    if ACTION in message and message[ACTION] == MESSAGE and SENDER in message and MESSAGE_TEXT in message:
        print(f'Получено сообщение от пользователя {message[SENDER]}:\n{message[MESSAGE_TEXT]}')
        logger.debug(f'Получено сообщение от пользователя {message[SENDER]}:\n{message[MESSAGE_TEXT]}')
    else:
        logger.error(f'Получено некорректное сообщение с сервера: {message}')


def main():
    server_address, server_port, client_name = parse_arguments()

    if not client_name:
        print('Консольный месседжер. Клиентский модуль.')
        client_name = input('Введите имя пользователя: ')
    else:
        print(f'Консольный месседжер. Клиентский модуль. Пользователь {client_name}')
    logger.info(f'Запущен клиент: {client_name}')
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((server_address, server_port))
        logger.info(f'Клиент {client_name} установил соединение с сервером. Адрес сервера: {server_address}, порт: {server_port}')
        send_message(sock, create_presence_message(user_name=client_name))
        answer = process_answer(get_message(sock))
        logger.info(f'Установлено соединение с сервером. Ответ сервера: {answer}')
        print(answer)
    except (ValueError, json.JSONDecodeError):
        logger.error('Не удалось декодировать полученную Json строку.')
        sys.exit(1)
    except OSError:
        logger.error('Ошибка соединения')
        sys.exit(1)
    except ConnectionRefusedError:
        logger.critical(f'Не удалось подключиться к серверу {server_address}:{server_port}')
        sys.exit(1)
    else:
        receiver = threading.Thread(target=message_from_server, args=(sock, client_name))
        receiver.daemon = True
        receiver.start()

        user_interface = threading.Thread(target=user_interactive, args=(sock, client_name))
        user_interface.daemon = True
        user_interface.start()
        logger.debug('Запущены процессы')

        while True:
            time.sleep(1)
            if receiver.is_alive() and user_interface.is_alive():
                continue
            break


if __name__ == '__main__':
    main()
