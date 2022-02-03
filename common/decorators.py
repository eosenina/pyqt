import sys
import logging
import logs.configs.server_logger_config
import logs.configs.client_logger_config
import inspect

if sys.argv[0].find('client') == -1:
    logger = logging.getLogger('server')
else:
    logger = logging.getLogger('client')


def log(function_to_log):
    def log_wrapper(*args, **kwargs):
        result = function_to_log(*args, **kwargs)
        logger.debug(f'Была вызвана функция {function_to_log.__name__} c параметрами {args}, {kwargs}. '
                     f'Вызов из модуля {function_to_log.__module__}. Вызов из функции {inspect.stack()[1][3]}', stacklevel=2)
        return result
    return log_wrapper


class Log:
    def __call__(self, function_to_log):
        def log_wrapper(*args, **kwargs):
            result = function_to_log(*args, **kwargs)
            logger.debug(f'Была вызвана функция {function_to_log.__name__} c параметрами {args}, {kwargs}. '
                         f'Вызов из модуля {function_to_log.__module__}. Вызов из функции {inspect.stack()[1][3]}', stacklevel=2)
            return result
        return log_wrapper
