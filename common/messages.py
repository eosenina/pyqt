import json
from common.settings import MAX_PACKAGE_LENGTH, ENCODING
from common.decorators import log


@log
def get_message(client):
    response = client.recv(MAX_PACKAGE_LENGTH)
    if isinstance(response, bytes):
        response = json.loads(response.decode(ENCODING))
        if isinstance(response, dict):
            return response
        raise ValueError
    raise ValueError


@log
def send_message(sock, message):
    sock.send(json.dumps(message).encode(ENCODING))
