import os
import sys
import unittest

sys.path.append(os.path.join(os.getcwd(), '..'))

from client import create_presence_message, process_answer
from common.settings import TIME, ACTION, PRESENCE, USER, ACCOUNT_NAME, ERROR, RESPONSE, STATUS, TYPE


class TestChatClient(unittest.TestCase):
    def test_create_presence_message_ok_default(self):
        test = create_presence_message()
        test[TIME] = 1.1
        self.assertEqual(test, {ACTION: PRESENCE, TIME: 1.1, TYPE: STATUS,
                                USER: {ACCOUNT_NAME: 'Guest', STATUS: 'I\'m here'}})

    def test_create_presence_message_ok_user(self):
        test = create_presence_message(user_name='Unicorn')
        test[TIME] = 1.1
        self.assertEqual(test, {ACTION: PRESENCE, TIME: 1.1, TYPE: STATUS,
                                USER: {ACCOUNT_NAME: 'Unicorn', STATUS: 'I\'m here'}})

    def test_create_presence_message_ok_status(self):
        test = create_presence_message(user_status='Unicorn')
        test[TIME] = 1.1
        self.assertEqual(test,
                         {ACTION: PRESENCE, TIME: 1.1, TYPE: STATUS, USER: {ACCOUNT_NAME: 'Guest', STATUS: 'Unicorn'}})

    def test_process_answer_ok(self):
        self.assertEqual(process_answer({RESPONSE: 200}), '200 : OK')

    def test_process_answer_err(self):
        self.assertEqual(process_answer({RESPONSE: 400, ERROR: 'Bad request'}), '400 : Bad request')

    def test_process_answer_no_response(self):
        self.assertRaises(ValueError, process_answer, {ERROR: 'Bad request'})


if __name__ == '__main__':
    unittest.main()
