import os
import sys
import unittest

sys.path.append(os.path.join(os.getcwd(), '..'))

from common.settings import RESPONSE, ERROR, USER, ACCOUNT_NAME, TIME, ACTION, PRESENCE, STATUS
from server import process_message


class TestChatServer(unittest.TestCase):
    test_resp_err = {
        RESPONSE: 400,
        ERROR: 'Bad request'
    }
    test_resp_ok = {RESPONSE: 200}

    def test_process_message_no_action(self):
        self.assertEqual(process_message(
            {TIME: '1.1', USER: {ACCOUNT_NAME: 'Guest', STATUS: 'I\'m here'}}), self.test_resp_err)

    def test_process_message_wrong_action(self):
        self.assertEqual(process_message(
            {ACTION: 'Something', TIME: '1.1', USER: {ACCOUNT_NAME: 'Guest'}}), self.test_resp_err)

    def test_process_message_no_time(self):
        self.assertEqual(process_message(
            {ACTION: PRESENCE, USER: {ACCOUNT_NAME: 'Guest', STATUS: 'I\'m here'}}), self.test_resp_err)

    def test_process_message_no_user(self):
        self.assertEqual(process_message(
            {ACTION: PRESENCE, TIME: '1.1'}), self.test_resp_err)

    def test_process_message_ok(self):
        self.assertEqual(process_message(
            {ACTION: PRESENCE, TIME: 1.1, USER: {ACCOUNT_NAME: 'Guest', STATUS: 'I\'m here'}}), self.test_resp_ok)


if __name__ == '__main__':
    unittest.main()
