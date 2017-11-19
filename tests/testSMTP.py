import sys
import os
import unittest
import unittest.mock as mc
import socket

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             os.path.pardir))
from smtp import SMTP


class MailMock:
    def __init__(self, name, sender, recipient, content):
        self.__name_f = name
        self.__sender_f = sender
        self.__recipient_f = recipient
        self.__content_f = content

    @property
    def name(self):
        return self.__name_f()

    @property
    def sender(self):
        return self.__sender_f()

    @property
    def recipient(self):
        return self.__recipient_f()

    def get_bytes(self):
        yield from self.__content_f()


class TestSMTP(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__tricky_500 = TestSMTP._generate_reply_fucntion(6, b'200 lol',
                                                              b'500 exter'
                                                              b'minate')
        self.__tricky_400 = TestSMTP._generate_reply_fucntion(4, b'200 lol',
                                                              b'400 wrong!')
        self.__cut_off_on_reply = \
            TestSMTP._generate_reply_function_that_cuts_off_connection(4)

    @staticmethod
    def _raise_(ex):
        raise ex

    @mc.patch('ssl.SSLSocket.sendall', lambda *args, **kwargs: None)
    @mc.patch('ssl.SSLSocket.recv',
              lambda *args, **kwargs: TestSMTP._raise_(socket.timeout()))
    @mc.patch('ssl.SSLSocket.connect', lambda *args, **kwargs: None)
    def test_fails_on_timeout(self):
        x = SMTP('127.0.0.1', 4000, '', '')
        interrupted, res = x.send([MailMock(lambda *args, **kwargs: "1",
                                            lambda *args, **kwargs: None,
                                            lambda *args, **kwargs: None,
                                            lambda *args, **kwargs: None)])
        self.assertTupleEqual((True,
                               ["Stopped with error: 'Connection timed out"
                                " while trying to receive a reply"
                                " from server'"]),
                              (interrupted, res))

    @mc.patch('ssl.SSLSocket.sendall', lambda *args, **kwargs: None)
    @mc.patch('ssl.SSLSocket.recv',
              lambda *args, **kwargs: '200')
    @mc.patch('ssl.SSLSocket.connect', lambda *args, **kwargs: TestSMTP
              ._raise_(socket.timeout()))
    def test_fails_on_timeout_when_connecting(self):
        x = SMTP('127.0.0.1', 4000, '', '')
        interrupted, res = x.send([MailMock(lambda *args, **kwargs: "1",
                                            lambda *args, **kwargs: None,
                                            lambda *args, **kwargs: None,
                                            lambda *args, **kwargs: None)])
        self.assertTupleEqual((True, ["Stopped with error: 'Timed out while"
                                      " establishing connection'"]),
                              (interrupted, res))

    @mc.patch('ssl.SSLSocket.sendall', lambda *args, **kwargs: None)
    @mc.patch('ssl.SSLSocket.recv',
              lambda *args, **kwargs: '200')
    @mc.patch('ssl.SSLSocket.connect', lambda *args, **kwargs: TestSMTP
              ._raise_(socket.error()))
    def test_fails_on_error_while_connecting(self):
        x = SMTP('127.0.0.1', 4000, '', '')
        interrupted, res = x.send([MailMock(lambda *args, **kwargs: "1",
                                            lambda *args, **kwargs: None,
                                            lambda *args, **kwargs: None,
                                            lambda *args, **kwargs: None)])
        self.assertTupleEqual((True, ["Stopped with error: 'Something went"
                                      " wrong while trying to establish"
                                      " connection ()'"]),
                              (interrupted, res))

    @mc.patch('ssl.SSLSocket.sendall', lambda *args, **kwargs: None)
    @mc.patch('ssl.SSLSocket.recv',
              lambda *args, **kwargs: b"200 lol")
    @mc.patch('ssl.SSLSocket.connect', lambda *args, **kwargs: None)
    def test_succeeds_on_all_200_replies(self):
        x = SMTP('127.0.0.1', 4000, '', '')
        interrupted, res = x.send([MailMock(lambda *args, **kwargs: "1",
                                            lambda *args, **kwargs: None,
                                            lambda *args, **kwargs: None,
                                            lambda *args, **kwargs: [b'a',
                                                                     b'b'])])
        self.assertTupleEqual((False, ["'1' sent"]), (interrupted, res))

    @staticmethod
    def _generate_reply_fucntion(num, message1, message2):
        iteration = -1

        def tricky_function(*args, **kwargs):
            nonlocal iteration
            iteration += 1
            if iteration == num:
                return message2
            return message1

        return tricky_function

    @staticmethod
    def _generate_reply_function_that_cuts_off_connection(num):
        iteration = -1

        def tricky_function(*args, **kwargs):
            nonlocal iteration
            iteration += 1
            if iteration >= num:
                return b''
            return b'200 lol'

        return tricky_function

    @mc.patch('ssl.SSLSocket.sendall', lambda *args, **kwargs: None)
    @mc.patch('ssl.SSLSocket.connect', lambda *args, **kwargs: None)
    def test_fails_on_500_reply_code_when_trying_to_send_a_message(self):
        with mc.patch(target='ssl.SSLSocket.recv', new=self.__tricky_500):
            x = SMTP('127.0.0.1', 4000, '', '')
            interrupted, res = x.send([MailMock(lambda *args, **kwargs: "1",
                                                lambda *args, **kwargs: None,
                                                lambda *args, **kwargs: None,
                                                lambda *args, **kwargs: [b'a',
                                                                         b'b']
                                                )])
            self.assertTupleEqual((False,
                                   ["'1' failed with error: 'exterminate'"]),
                                  (interrupted, res))

    @mc.patch('ssl.SSLSocket.sendall', lambda *args, **kwargs: None)
    @mc.patch('ssl.SSLSocket.connect', lambda *args, **kwargs: None)
    def test_fails_on_cut_off_connection(self):
        with mc.patch(target='ssl.SSLSocket.recv',
                      new=self.__cut_off_on_reply):
            x = SMTP('127.0.0.1', 4000, '', '')
            interrupted, res = x.send([MailMock(lambda *args, **kwargs: "1",
                                                lambda *args, **kwargs: None,
                                                lambda *args, **kwargs: None,
                                                lambda *args, **kwargs: [b'a',
                                                                         b'b']
                                                )])
            self.assertTupleEqual((True,
                                   ["Stopped with error:"
                                    " 'Connection shut down"
                                    " by the other side'"]),
                                  (interrupted, res))


if __name__ == '__main__':
    unittest.main()
