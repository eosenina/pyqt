import logging

DEFAULT_PORT = 7777
DEFAULT_IP_ADDRESS = '127.0.0.1'
MAX_CONNECTIONS = 5
MAX_PACKAGE_LENGTH = 1024
ENCODING = 'utf-8'

# Ключи протокола:
ACTION = 'action'
TIME = 'time'
USER = 'user'
ACCOUNT_NAME = 'account_name'
PRESENCE = 'presence'
RESPONSE = 'response'
ERROR = 'error'
STATUS = 'status'
TYPE = 'type'
MESSAGE = 'message'
MESSAGE_TEXT = 'message_text'
SENDER = 'sender'
DESTINATION = 'destination'
EXIT = 'exit'

LOGGING_LEVEL = logging.DEBUG
