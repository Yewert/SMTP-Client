import re
import pathlib


class LetterParser:
    def __init__(self, path):
        self.__subject = None
        self.__recipients = None
        self.__type = None
        self.__path = path
        self.__attachments = []
        self.__offset = 0

    __recipient_pattern = re.compile(r'^To:', re.IGNORECASE)
    __email_address = re.compile(
        r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
    __subject_pattern = re.compile(r'^subject:\s?(.*)', re.IGNORECASE)
    __attachment_pattern = re.compile(r'^attachment:\s?(.*)', re.IGNORECASE)
    __type_pattern = re.compile(r'type:\s?(plain|html)', re.IGNORECASE)

    def parse_lines(self, lines):
        for index, line in lines:
            if index == 0:
                match = LetterParser.__recipient_pattern.match(line)
                if match is None:
                    raise MailParsingException("Expected to"
                                               " find recipient"
                                               " in line 0,"
                                               " found : '{}'"
                                               .format(line))
                self.__recipients = LetterParser.__email_address.findall(line)
            if index == 1:
                match = LetterParser.__type_pattern.match(line)
                if match is None:
                    raise MailParsingException("Expected to"
                                               " find type"
                                               " in line 1,"
                                               " found : '{}'"
                                               .format(line))
                self.__type = match.group(1)
            if index == 2:
                match = LetterParser.__subject_pattern.match(line)
                if match is None:
                    raise MailParsingException("Expected to"
                                               " find subject"
                                               " in line 2,"
                                               " found : '{}'"
                                               .format(line))
                self.__subject = match.group(1)
            if index > 2:
                match = LetterParser.__attachment_pattern.match(line)
                if match is None:
                    return
                self.__attachments.append((index,
                                           pathlib.Path(match.group(1))))
            self.__offset += 1

    def get_letter_attributes(self):
        for recipient in self.__recipients:
            yield self.__path, recipient, self.__type, self.__subject, \
                  self.__attachments, lambda: \
                  (yield from self.__get_text_function())

    def __get_text_function(self):
        with open(self.__path, 'rb') as file:
            for index, line in enumerate(file):
                if index >= self.__offset:
                    yield line


class MailParsingException(Exception):
    pass


if __name__ == '__main__':
    pass
