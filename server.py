import select
import socket
import sys
import logging
import threading
import time

from common.settings import MAX_CONNECTIONS, DEFAULT_PORT, ACTION, RESPONSE, ERROR, PRESENCE, TIME, USER, MESSAGE, \
    MESSAGE_TEXT, SENDER, ACCOUNT_NAME, DESTINATION, EXIT
from common.messages import get_message, send_message
from common.decorators import log
from common.descr import Port
from common.meta import ServerMaker
from server_db import ServerStorage

logger = logging.getLogger('server')


def parse_arguments():
    try:
        if '-p' in sys.argv:
            port = int(sys.argv[sys.argv.index('-p') + 1])
        else:
            port = DEFAULT_PORT
        if port < 1024 or port > 65535:
            raise ValueError
    except IndexError:
        logger.critical('Не указан номер порта.')
        sys.exit(1)
    except ValueError:
        logger.critical(
            f'Недопустимое значение порта {port}. Диапазон допустимых значений для порта: от 1024 до 65535.')
        sys.exit(1)

    try:
        if '-a' in sys.argv:
            address = sys.argv[sys.argv.index('-a') + 1]
        else:
            address = ''
    except IndexError:
        logger.critical('Не указан адрес.')
        sys.exit(1)
    return address, port


class Server(threading.Thread, metaclass=ServerMaker):
    port = Port()

    def __init__(self, address, port, database):
        self.address = address
        self.port = port
        self.clients_list = []
        self.messages_list = []
        self.user_names_dict = dict()
        self.database = database
        super().__init__()

    def process_incoming_message(self, message, messages_list, client, clients_list, user_names_dict):
        logger.debug(f'Разбор сообщения от клиента : {message}')
        if ACTION in message and message[ACTION] == PRESENCE and TIME in message and USER in message:
            if message[USER][ACCOUNT_NAME] not in user_names_dict.keys():
                user_names_dict[message[USER][ACCOUNT_NAME]] = client
                ip, port = client.getpeername()
                self.database.user_login(message[USER][ACCOUNT_NAME], ip, port)
                send_message(client, {RESPONSE: 200})
            else:
                response = {RESPONSE: 400, ERROR: 'Имя пользователя уже занято.'}
                send_message(client, response)
                clients_list.remove(client)
                client.close()
            return
        elif ACTION in message and message[ACTION] == MESSAGE and DESTINATION in message and TIME in message \
                and SENDER in message and MESSAGE_TEXT in message:
            messages_list.append(message)
            return
        elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME in message:
            self.database.user_logout(message[ACCOUNT_NAME])
            clients_list.remove(user_names_dict[message[ACCOUNT_NAME]])
            user_names_dict[message[ACCOUNT_NAME]].close()
            del user_names_dict[message[ACCOUNT_NAME]]
            return
        else:
            send_message(client, {RESPONSE: 400, ERROR: 'Запрос некорректен.'})
            return

    def process_message_to_send(self, message, user_names_list, listen_socks):
        if message[DESTINATION] in user_names_list and user_names_list[message[DESTINATION]] in listen_socks:
            send_message(user_names_list[message[DESTINATION]], message)
            logger.info(f'Отправлено сообщение пользователю {message[DESTINATION]} от пользователя {message[SENDER]}.')
        elif message[DESTINATION] in user_names_list and user_names_list[message[DESTINATION]] not in listen_socks:
            raise ConnectionError
        else:
            logger.error(f'Пользователь {message[DESTINATION]} не зарегистрирован, отправка сообщения невозможна.')

    def run(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.address, self.port))
        server_socket.settimeout(1)
        server_socket.listen(MAX_CONNECTIONS)
        logger.info(f'Сервер запущен\nАдрес: {self.address}\nПорт: {self.port}')

        while True:
            try:
                client, client_address = server_socket.accept()
            except OSError:
                pass
            else:
                logger.info(f'Установлено соедение с клиентом {client_address}')
                self.clients_list.append(client)

            read_data_list = []
            write_data_list = []
            error_list = []
            try:
                if self.clients_list:
                    read_data_list, write_data_list, error_list = select.select(self.clients_list, self.clients_list, [], 0)
            except OSError:
                pass

            if read_data_list:
                for client_to_read in read_data_list:
                    try:
                        self.process_incoming_message(get_message(client_to_read), self.messages_list, client_to_read, self.clients_list, self.user_names_dict)
                    except OSError:
                        logger.info(f'Клиент {client_to_read.getpeername()} отключился от сервера.')
                        self.clients_list.remove(client_to_read)

            for msg in self.messages_list:
                try:
                    self.process_message_to_send(msg, self.user_names_dict, write_data_list)
                except Exception:
                    logger.info(f'Связь с клиентом с именем {msg[DESTINATION]} была потеряна')
                    self.clients_list.remove(self.user_names_dict[msg[DESTINATION]])
                    del self.user_names_dict[msg[DESTINATION]]
            self.messages_list.clear()


def print_help():
    print('Поддерживаемые комманды:')
    print('users - список пользователей')
    print('connected - список подключенных пользователей')
    print('history - история входов пользователя')
    print('exit - завершение работы сервера')
    print('help - вывод справки')


if __name__ == '__main__':
    addr, port = parse_arguments()
    database = ServerStorage()

    server = Server(addr, port, database)
    server.daemon = True
    server.start()

    print_help()
    while True:
        command = input('Введите комманду: ')
        if command == 'help':
            print_help()
        elif command == 'exit':
            break
        elif command == 'users':
            for user in sorted(database.users_list()):
                print(f'Пользователь {user[0]}, последний вход: {user[1]}')
        elif command == 'connected':
            for user in sorted(database.active_users_list()):
                print(f'Пользователь {user[0]}, подключен: {user[1]}:{user[2]}, время установки соединения: {user[3]}')
        elif command == 'history':
            name = input('Введите имя пользователя. Для вывода всей истории - нажмите Enter: ')
            for user in sorted(database.login_history(name)):
                print(f'Пользователь: {user[0]} время входа: {user[1]}. Вход с: {user[2]}:{user[3]}')
        else:
            print('Команда не распознана.')


