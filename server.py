import select
import socket
import sys
import json
import logging
import time

import logs.configs.server_logger_config
from common.settings import MAX_CONNECTIONS, DEFAULT_PORT, ACTION, RESPONSE, ERROR, PRESENCE, TIME, USER, MESSAGE, \
    MESSAGE_TEXT, SENDER, ACCOUNT_NAME, DESTINATION, EXIT
from common.messages import get_message, send_message
from common.decorators import log

logger = logging.getLogger('server')


class Server:

    def process_incoming_message(self, message, messages_list, client, clients_list, user_names_dict):
        logger.debug(f'Разбор сообщения от клиента : {message}')
        if ACTION in message and message[ACTION] == PRESENCE and TIME in message and USER in message:
            if message[USER][ACCOUNT_NAME] not in user_names_dict.keys():
                user_names_dict[message[USER][ACCOUNT_NAME]] = client
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

    def main_loop(self):
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
            logger.critical(f'Недопустимое значение порта {port}. Диапазон допустимых значений для порта: от 1024 до 65535.')
            sys.exit(1)

        try:
            if '-a' in sys.argv:
                address = sys.argv[sys.argv.index('-a') + 1]
            else:
                address = ''
        except IndexError:
            logger.critical('Не указан адрес.')
            sys.exit(1)

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((address, port))
        server_socket.settimeout(1)
        server_socket.listen(MAX_CONNECTIONS)
        logger.info(f'Сервер запущен\nАдрес: {address}\nПорт: {port}')

        clients_list = []
        messages_list = []

        user_names_dict = dict()

        while True:
            try:
                client, client_address = server_socket.accept()
            except OSError:
                pass
            else:
                logger.info(f'Установлено соедение с клиентом {client_address}')
                clients_list.append(client)

            read_data_list = []
            write_data_list = []
            error_list = []
            try:
                if clients_list:
                    read_data_list, write_data_list, error_list = select.select(clients_list, clients_list, [], 0)
            except OSError:
                pass

            if read_data_list:
                for client_to_read in read_data_list:
                    try:
                        self.process_incoming_message(get_message(client_to_read), messages_list, client_to_read, clients_list, user_names_dict)
                    except OSError:
                        logger.info(f'Клиент {client_to_read.getpeername()} отключился от сервера.')
                        clients_list.remove(client_to_read)

            for msg in messages_list:
                try:
                    self.process_message_to_send(msg, user_names_dict, write_data_list)
                except Exception:
                    logger.info(f'Связь с клиентом с именем {msg[DESTINATION]} была потеряна')
                    clients_list.remove(user_names_dict[msg[DESTINATION]])
                    del user_names_dict[msg[DESTINATION]]
            messages_list.clear()


if __name__ == '__main__':
    serv = Server()
    serv.main_loop()
