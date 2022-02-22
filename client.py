import argparse
import sys
import json
import socket
import time
import logging
import threading
import logs.configs.client_logger_config
from client_db import ClientDatabase
from common.settings import ACTION, PRESENCE, DEFAULT_IP_ADDRESS, DEFAULT_PORT, RESPONSE, ERROR, TIME, USER, \
    ACCOUNT_NAME, TYPE, STATUS, MESSAGE, MESSAGE_TEXT, SENDER, DESTINATION, EXIT, ADD_CONTACT, GET_CONTACTS, LIST_INFO, \
    REGISTERED_USERS, DEL_CONTACT
from common.messages import get_message, send_message
from common.decorators import Log
from common.meta import ClientMaker

logger = logging.getLogger('client')

sock_lock = threading.Lock()
database_lock = threading.Lock()


class ClientSender(threading.Thread, metaclass=ClientMaker):
    def __init__(self, sock, database, user_name='Guest'):
        self.user_name = user_name
        self.sock = sock
        self.database = database
        super().__init__()

    def run(self):
        while True:
            command = input('Введите команду: msg - отправить сообщение, '
                            'q - выход, c - список контактов, e - редактирование контактов, h - история сообщений: ')
            if command == 'msg':
                self.create_message()
            elif command == 'q':
                send_message(self.sock, self.create_exit_message())
                print('Завершение соединения.')
                logger.info('Завершение работы по команде пользователя.')
                time.sleep(0.5)
                break
            elif command == 'c':
                with database_lock:
                    contacts_list = self.database.get_contacts()
                for contact in contacts_list:
                    print(contact)
            elif command == 'e':
                self.edit_contacts()
            elif command == 'h':
                self.print_history()
            else:
                print('Команда не распознана, попробойте снова.')

    def edit_contacts(self):
        choice = input('Для удаления введите del, для добавления add: ')
        if choice == 'del':
            name = input('Введите имя удаляемного контакта: ')
            with database_lock:
                if self.database.check_contact(name):
                    self.database.del_contact(name)
                else:
                    logger.error('Попытка удаления несуществующего контакта.')
        elif choice == 'add':
            name = input('Введите имя создаваемого контакта: ')
            if self.database.check_user(name):
                with database_lock:
                    self.database.add_contact(name)
                with sock_lock:
                    add_contact(self.sock, self.user_name, name)

    def print_history(self):
        choice = input('Показать входящие сообщения - in, исходящие - out, все сообщения - любую клавишу: ')
        with database_lock:
            if choice == 'in':
                history_list = self.database.get_history(recipient=self.user_name)
                for message in history_list:
                    print(f'\nСообщение от пользователя: {message[0]} от {message[3]}:\n{message[2]}')
            elif choice == 'out':
                history_list = self.database.get_history(sender=self.user_name)
                for message in history_list:
                    print(f'\nСообщение пользователю: {message[1]} от {message[3]}:\n{message[2]}')
            else:
                history_list = self.database.get_history()
                for message in history_list:
                    print(f'\nСообщение от пользователя: {message[0]}, пользователю {message[1]} от {message[3]}\n{message[2]}')

    def create_message(self):
        recipient = input('Введите получателя сообщения: ')
        message_text = input('Введите текст сообщения: ')

        with database_lock:
            if not self.database.check_user(recipient):
                logger.error(f'Попытка отправить сообщение незарегистрированому получателю: {recipient}')
                return

        message_dict = {
            ACTION: MESSAGE,
            SENDER: self.user_name,
            DESTINATION: recipient,
            TIME: time.time(),
            MESSAGE_TEXT: message_text
        }
        logger.debug(f'Сформировано сообщение: {message_dict}')

        with database_lock:
            self.database.save_message(self.user_name, recipient, message_text)

        with sock_lock:
            try:
                send_message(self.sock, message_dict)
                logger.info(f'Отправлено сообщение для пользователя {recipient}')
            except OSError:
                logger.critical('Потеряно соединение с сервером.')
                sys.exit(1)

    def create_exit_message(self):
        return {
            ACTION: EXIT,
            TIME: time.time(),
            ACCOUNT_NAME: self.user_name
        }


class ClientReceiver(threading.Thread, metaclass=ClientMaker):
    def __init__(self, sock, database, user_name):
        self.user_name = user_name
        self.sock = sock
        self.database = database
        super().__init__()

    def run(self):
        while True:
            time.sleep(1)
            while sock_lock:

                try:
                    message = get_message(self.sock)
                    if ACTION in message and message[ACTION] == MESSAGE and SENDER in message and DESTINATION in message \
                            and MESSAGE_TEXT in message and message[DESTINATION] == self.user_name:
                        print(f'\nПолучено сообщение от пользователя {message[SENDER]}:\n{message[MESSAGE_TEXT]}')
                        with database_lock:
                            try:
                                self.database.save_message(message[SENDER], self.user_name, message[MESSAGE_TEXT])
                            except:
                                logger.error('Ошибка взаимодействия с базой данных')
                        logger.info(f'Получено сообщение от пользователя {message[SENDER]}:\n{message[MESSAGE_TEXT]}')
                    else:
                        logger.error(f'Получено некорректное сообщение с сервера: {message}')
                except (OSError, ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError):
                    logger.critical(f'Потеряно соединение с сервером.')
                    break


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
def process_answer(message):
    if RESPONSE in message:
        if message[RESPONSE] == 200:
            return '200 : OK'
        return f'400 : {message[ERROR]}'
    raise ValueError


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


def add_contact(sock, username, contact):
    logger.debug(f'Создание контакта {contact}')
    request = {
        ACTION: ADD_CONTACT,
        TIME: time.time(),
        USER: username,
        ACCOUNT_NAME: contact
    }
    send_message(sock, request)
    ans = get_message(sock)
    if RESPONSE in ans and ans[RESPONSE] == 200:
        print('Удачное создание контакта.')
    else:
        print('Ошибка создания контакта')
        logger.error('Не удалось отправить информацию на сервер.')


def contacts_list_request(sock, name):
    logger.debug(f'Запрос контакт листа для пользователся {name}')
    request = {
        ACTION: GET_CONTACTS,
        TIME: time.time(),
        USER: name
    }
    logger.debug(f'Сформирован запрос {request}')
    send_message(sock, request)
    answer = get_message(sock)
    logger.debug(f'Получен ответ {answer}')
    if RESPONSE in answer and answer[RESPONSE] == 202:
        return answer[LIST_INFO]
    else:
        raise ValueError


def user_list_request(sock, username):
    logger.debug(f'Запрос списка известных пользователей {username}')
    request = {
        ACTION: REGISTERED_USERS,
        TIME: time.time(),
        ACCOUNT_NAME: username
    }
    send_message(sock, request)
    answer = get_message(sock)
    if RESPONSE in answer and answer[RESPONSE] == 202:
        return answer[LIST_INFO]
    else:
        raise ValueError


def remove_contact(sock, username, contact):
    logger.debug(f'Создание контакта {contact}')
    request = {
        ACTION: DEL_CONTACT,
        TIME: time.time(),
        USER: username,
        ACCOUNT_NAME: contact
    }
    send_message(sock, request)
    answer = get_message(sock)
    if RESPONSE in answer and answer[RESPONSE] == 200:
        print('Контакт удалён')
    else:
        raise ValueError('Ошибка удаления клиента')


def database_load(sock, database, username):
    try:
        users_list = user_list_request(sock, username)
    except ValueError:
        logger.error('Ошибка запроса списка известных пользователей.')
    else:
        database.add_users(users_list)

    try:
        contacts_list = contacts_list_request(sock, username)
    except ValueError:
        logger.error('Ошибка запроса списка контактов.')
    else:
        for contact in contacts_list:
            database.add_contact(contact)


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
        logger.info(
            f'Клиент {client_name} установил соединение с сервером. Адрес сервера: {server_address}, порт: {server_port}')
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

        database = ClientDatabase(client_name)
        database_load(sock, database, client_name)

        receiver = ClientReceiver(sock, client_name)
        receiver.daemon = True
        receiver.start()

        user_interface = ClientSender(sock, client_name)
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
