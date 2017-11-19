class ConnectionException(Exception):
    pass


class ConnectionTimedOutException(ConnectionException):
    pass


class ConnectionLostException(ConnectionException):
    pass


class ConnectionShutDownException(ConnectionException):
    pass


if __name__ == '__main__':
    pass
