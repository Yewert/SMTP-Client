import base64
import random
import re
import string
import quopri
from functools import reduce


class Mail:
    def __init__(self, aliases,  sender, name, recipient, type, subject, attachments,
                 get_text):

        self.__name = name + ' to ' + recipient
        self.__aliases = aliases
        self.__sender = sender
        self.__type = type
        self.__recipient = recipient
        self.__subject = subject
        self.__indexes_and_attachments = attachments
        self.__get_text = get_text
        self.__boundary = '--' + ''.join(
            random.choice(string.ascii_letters) for x in range(20))
        self.__header = 'From:{}\r\n' \
                        'To:{}\r\n' \
                        'Subject:{}\r\n' \
                        'MIME-Version: 1.0\r\n' \
                        'Content-type: multipart/mixed;' \
                        ' boundary="{b}"\r\n\r\n' \
                        '--{b}\r\n'\
            .format(self.__sender, self.__recipient,
                    self.__subject, b=self.__boundary[2:]) \
            .encode()
                        # 'Content-type: text/plain; charset="UTF-8"\r\n\r\n' \
        self.__ending = '{}--'.format(self.__boundary).encode()

    @property
    def recipient(self):
        return self.__recipient

    @property
    def sender(self):
        return self.__sender

    @property
    def name(self):
        return self.__name

    def get_bytes(self):
        yield self.__header
        lines = reduce(lambda x, y: x + y, self.__get_text()).decode()
        for regex, substitute in self.__aliases:
            lines = regex.sub(substitute, lines)
        lines = quopri.encodestring(lines.encode())
        if self.__type == "html":
            yield 'Content-Type: text/html; charset=utf-8\r\n' \
                  'Content-Transfer-Encoding: quoted-printable\r\n\r\n'\
                      .encode() + lines
        if self.__type == "plain":
            yield 'Content-Type: text/plain; charset=utf-8\r\n' \
                  'Content-Transfer-Encoding: quoted-printable\r\n\r\n'\
                      .encode() + lines
        yield b'\r\n'
        for index_and_attachment in self.__indexes_and_attachments:
            yield self.__boundary.encode() + b'\r\n'
            for block in Mail.__get_attachment_content(*index_and_attachment):
                yield block
        yield self.__ending

    @staticmethod
    def __validate_attachment(index, attachment):
        if not attachment.exists():
            raise AttachmentNotFoundException("Attachment in line {}"
                                              " not found".format(index))
        if attachment.is_dir():
            raise AttachmentIsADirectoryException("Expected"
                                                  " to find a path"
                                                  " to file in"
                                                  " line {},"
                                                  " found a "
                                                  "directory"
                                                  .format(index))

    @staticmethod
    def __get_attachment_content(index, attachment):
        Mail.__validate_attachment(index, attachment)
        yield 'Content-type: application/octet-stream\r\n' \
              'Content-Disposition: attachment; ' \
              'filename="{}"\r\n' \
              'Content-transfer-encoding: base64\r\n\r\n'.format(
                attachment.name).encode()
        try:
            with open(str(attachment), 'br') as file:
                yield base64.b64encode(file.read())
        except PermissionError as e:
            raise AttachmentPermissionException("Couldn't open"
                                                " attachment in line {} ({})"
                                                .format(index, str(e)))
        yield b'\r\n\r\n'


class MailLoadingException(Exception):
    pass


class AttachmentLoadingException(MailLoadingException):
    pass


class AttachmentNotFoundException(AttachmentLoadingException):
    pass


class AttachmentIsADirectoryException(AttachmentLoadingException):
    pass


class AttachmentPermissionException(AttachmentLoadingException):
    pass


class MailPermissionException(MailLoadingException):
    pass


if __name__ == '__main__':
    pass
