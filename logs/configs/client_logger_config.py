import sys
import os
import logging
sys.path.append(os.path.join(os.getcwd(), '../../'))
from common.settings import LOGGING_LEVEL


client_formatter = logging.Formatter('%(asctime)s %(levelname)s %(filename)s %(message)s')
log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../log_files/client.log')

stream_h = logging.StreamHandler(sys.stderr)
stream_h.setFormatter(client_formatter)
stream_h.setLevel(logging.ERROR)
log_file = logging.FileHandler(log_file_path, encoding='utf8')
log_file.setFormatter(client_formatter)

client_logger = logging.getLogger('client')
client_logger.addHandler(stream_h)
client_logger.addHandler(log_file)
client_logger.setLevel(LOGGING_LEVEL)

if __name__ == '__main__':
    client_logger.critical('Критическая ошибка')
    client_logger.error('Ошибка')
    client_logger.debug('Отладочная информация')
    client_logger.info('Информационное сообщение')
