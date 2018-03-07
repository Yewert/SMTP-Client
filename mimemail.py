import base64
import random
import re
import string
import quopri
from functools import reduce


class Mail:
    def __init__(self, aliases, sender, name, recipient, markup_type, subject,
                 attachments,
                 get_text):

        self.__aliases = aliases
        self.__name = name + ' to ' + recipient
        self.__sender = sender
        self.__type = markup_type
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
                        '--{b}\r\n' \
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
        for pattern in self.__aliases.keys():
            lines = re.sub('%{}%'.format(pattern),
                           self.__aliases[pattern](self.recipient), lines)
        lines = base64.b64encode(lines.encode())
        if self.__type == "html":
            yield 'Content-Type: text/html; charset=utf-8\r\n' \
                  'Content-Transfer-Encoding: base64\r\n\r\n' \
                .encode() + lines
        if self.__type == "plain":
            yield 'Content-Type: text/plain; charset=utf-8\r\n' \
                  'Content-Transfer-Encoding: base64\r\n\r\n' \
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
            raise MailLoadingException("Attachment in line {}"
                                       " not found".format(index))
        if attachment.is_dir():
            raise MailLoadingException("Expected"
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
            raise MailLoadingException("Couldn't open"
                                       " attachment in line {} ({})"
                                       .format(index, str(e)))
        yield b'\r\n\r\n'


class MailLoadingException(Exception):
    pass


if __name__ == '__main__':
    pass
