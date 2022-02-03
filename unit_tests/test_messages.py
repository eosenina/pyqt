import os
import sys
import unittest
import json

sys.path.append(os.path.join(os.getcwd(), '..'))

from common.settings import RESPONSE, ERROR, USER, ACCOUNT_NAME, TIME, ACTION, PRESENCE, ENCODING
from common.messages import get_message, send_message


class TestSocket:
    def __init__(self, test_dict):
        self.test_dict = test_dict
        self.encoded_msg = None
        self.received_msg = None

    def send(self, message):
        self.encoded_msg = json.dumps(self.test_dict).encode(ENCODING)
        self.received_msg = message

    def recv(self, max_len):
        return json.dumps(self.test_dict).encode(ENCODING)


class TestMessages(unittest.TestCase):
    test_dict = {
        ACTION: PRESENCE,
        TIME: 111.111,
        USER: {
            ACCOUNT_NAME: 'test_test'
        }
    }
    test_resp_ok = {RESPONSE: 200}
    test_resp_err = {
        RESPONSE: 400,
        ERROR: 'Bad Request'
    }

    def test_send_message_ok(self):
        test_socket = TestSocket(self.test_dict)
        send_message(test_socket, self.test_dict)
        self.assertEqual(test_socket.encoded_msg, test_socket.received_msg)

    def test_seng_message_none_sock(self):
        with self.assertRaises(Exception):
            send_message(None, self.test_dict)

    def test_get_message_ok(self):
        test_sock_ok = TestSocket(self.test_resp_ok)
        self.assertEqual(get_message(test_sock_ok), self.test_resp_ok)

    def test_get_message_err_dict(self):
        test_sock_err = TestSocket(self.test_resp_err)
        self.assertEqual(get_message(test_sock_err), self.test_resp_err)


if __name__ == '__main__':
    unittest.main()
