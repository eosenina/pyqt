import sys
import os
import logging.handlers
sys.path.append(os.path.join(os.getcwd(), '../../'))
from common.settings import LOGGING_LEVEL


server_formatter = logging.Formatter('%(asctime)s %(levelname)s %(filename)s %(message)s')
log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../log_files/server.log')

stream_h = logging.StreamHandler(sys.stderr)
stream_h.setFormatter(server_formatter)
stream_h.setLevel(logging.ERROR)
log_file = logging.handlers.TimedRotatingFileHandler(log_file_path, encoding='utf8', interval=1, when='D')
log_file.setFormatter(server_formatter)

server_logger = logging.getLogger('server')
server_logger.addHandler(stream_h)
server_logger.addHandler(log_file)
server_logger.setLevel(LOGGING_LEVEL)

if __name__ == '__main__':
    server_logger.critical('Критическая ошибка')
    server_logger.error('Ошибка')
    server_logger.debug('Отладочная информация')
    server_logger.info('Информационное сообщение')
