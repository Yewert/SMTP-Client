import socket
import ssl
import base64
import connexceptions
import mimemail


class SMTP:
    __BUFFER_SIZE = 1024
    __MAX_ERROR = 10
    __STANDARD_REPLY_TIMEOUT = 10

    def __init__(self, address, port, login, password, debug=False):
        self.__connection_error_count = 0
        self.__address = address
        self.__port = port
        self.__login = login
        self.__password = password
        self.__debug = debug

    def __log_in(self):
        soc = None
        try:
            soc = self.__connect()
            for command in SMTP.__authentification:
                self.__handle_reply(soc, SMTP.__STANDARD_REPLY_TIMEOUT)
                self.__handle_sending(soc, command(self) + b'\r\n', None)
            else:
                self.__handle_reply(soc, SMTP.__STANDARD_REPLY_TIMEOUT)
        except (connexceptions.ConnectionException, SmtpException) as e:
            if soc is not None:
                soc.close()
            return None, e
        return soc, None

    __authentification = [
        lambda x: 'EHLO {}'.format(x.__login).encode(),
        lambda x: b'AUTH LOGIN',
        lambda x: base64.b64encode(x.__login.encode()),
        lambda x: base64.b64encode(x.__password.encode())
    ]

    def __connect(self):
        soc = ssl.wrap_socket(socket.socket())
        try:
            soc.settimeout(SMTP.__STANDARD_REPLY_TIMEOUT)
            soc.connect((self.__address, self.__port))
        except socket.timeout:
            soc.close()
            raise connexceptions.ConnectionException(
                "Timed out while establishing connection")
        except Exception as e:
            soc.close()
            raise connexceptions.ConnectionException("Something went wrong"
                                                     " while trying to"
                                                     " establish connection "
                                                     "({})".format(str(e)))
        else:
            soc.settimeout(None)
            return soc

    def send(self, mails):
        delivery_results = []
        soc, exc = self.__log_in()
        if soc is None:
            return True, ["Stopped with error: '{}'".format(str(exc))]
        for index, mail in enumerate(mails):
            try:
                self.__handle_sending(soc,
                                      'MAIL FROM: {}\r\n'.format(mail.sender)
                                      .encode(),
                                      None)
                self.__handle_reply(soc, SMTP.__STANDARD_REPLY_TIMEOUT)
                self.__handle_sending(soc,
                                      'RCPT TO: {}\r\n'.format(mail.recipient)
                                      .encode(),
                                      None)
                self.__handle_reply(soc, SMTP.__STANDARD_REPLY_TIMEOUT)
                self.__handle_sending(soc, b'DATA\r\n', None)
                self.__handle_reply(soc, SMTP.__STANDARD_REPLY_TIMEOUT)
                for chunk in mail.get_bytes():
                    self.__handle_sending(soc, chunk, None)
                self.__handle_sending(soc, b'\r\n.\r\n', None)
                self.__handle_reply(soc, SMTP.__STANDARD_REPLY_TIMEOUT)
            except (SmtpException, mimemail.MailLoadingException) as e:
                delivery_results.append("'{}' failed with error: '{}'"
                                        .format(mail.name, str(e)))
                soc.close()
                soc, exc = self.__log_in()
                if soc is None:
                    delivery_results.append("Stopped on '{}' with error: '{}'"
                                            .format(mail.name, str(exc)))
                    return True, delivery_results
                continue
            except connexceptions.ConnectionException as e:
                delivery_results.append("Stopped on '{}' with error: '{}'"
                                        .format(mail.name, str(e)))
                soc.close()
                return True, delivery_results
            else:
                delivery_results.append("'{}' sent".format(mail.name))
        while True:
            soc.sendall(b'QUIT\r\n')
            data = soc.recv(SMTP.__BUFFER_SIZE).decode()
            if data[0] != '5':
                break
        soc.close()
        return False, delivery_results

    def __handle_sending(self, connection_socket, data_to_transmit, timeout):
        if self.__debug:
            print("->" + data_to_transmit[0:30].decode())
        connection_socket.settimeout(timeout)
        try:
            connection_socket.sendall(data_to_transmit)
        except socket.timeout:
            raise connexceptions.ConnectionException("Connection"
                                                     " timed out"
                                                     " while trying"
                                                     " to send"
                                                     " data to server")
        except socket.error as e:
            raise connexceptions.ConnectionException(str(e))

    def __handle_reply(self, connection_socket, timeout):
        connection_socket.settimeout(timeout)
        try:
            data = connection_socket.recv(SMTP.__BUFFER_SIZE)
            if self.__debug:
                print("<---" + data.decode())
        except socket.timeout:
            connection_socket.close()
            raise connexceptions.ConnectionException("Connection"
                                                     " timed out"
                                                     " while trying"
                                                     " to receive"
                                                     " a reply"
                                                     " from server")
        except socket.error as e:
            connection_socket.close()
            raise connexceptions.ConnectionException(str(e))

        if data == b'':
            connection_socket.close()
            raise connexceptions.ConnectionException("Connection"
                                                     " shut down by "
                                                     "the other side")
        self.__handle_reply_code(data)
        connection_socket.settimeout(None)

    @staticmethod
    def __handle_reply_code(message):
        code = message[:3].decode()
        if code[0] == '2' or code[0] == '3':
            return
        if code[0] == '4':
            raise SmtpException(message[3:].decode().lstrip())
        if code[0] == '5':
            raise SmtpException(message[3:].decode().lstrip())


class SmtpException(Exception):
    pass


if __name__ == '__main__':
    pass
