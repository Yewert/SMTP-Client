import re
import sys

import aliasloader
import smtp
import mimemail
import letterparser
import argparse
import pathlib


def iterate_file(path):
    with open(path, 'rb') as file:
        for index, line in enumerate(file):
            yield index, re.sub(r'[\n\r]', '', line.decode())


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-d', '--debug', action='store_true', default=False,
                        dest='debug', help='Enable debug mode')
    options = parser.add_mutually_exclusive_group(required=True)
    options.add_argument('-s', '--single',
                         action='store',
                         dest='pathToSingleMail',
                         help='Single mail',
                         type=str)
    options.add_argument('-m', '--multiple',
                         action='store',
                         dest='pathToFolderWithMails',
                         help='Folder with mails',
                         type=str)
    result_of_parsing = parser.parse_args()
    try:
        user_info = pathlib.Path("./userinfo.usrinf")
        user_info.resolve()
        with open(str(user_info), 'r') as ui:
            lines = ui.readlines()
            server = re.sub(r'[\r\n]', '', lines[0])
            port = int(lines[1])
            login = re.sub(r'[\r\n]', '', lines[2])
            password = re.sub(r'[\r\n]', '', lines[3])
    except FileNotFoundError:
        print("Could not find configuration file")
        sys.exit(1)
    except PermissionError:
        print("Did not have enough permissions to read configuration file")
        sys.exit(1)
    except (IndexError, ValueError):
        print("Configuration file had wrong formatting (see 'readme.md'")
        sys.exit(1)

    try:
        aliases_path = pathlib.Path("./aliases.usrinf")
        aliases_path.resolve()
        with open(str(aliases_path), 'rb') as al:
            lines = list(map(lambda x: x.decode(), al.readlines()))
            pattern = re.compile(r'^([\w\d]+):([\w\d]+);')
            loader = aliasloader.AliasLoader(lambda x: pattern.match(x))
            aliases = loader.get_alias_substitution_list(lines)
    except (FileNotFoundError, PermissionError, ValueError) as e:
        if result_of_parsing.debug:
            print(str(e))
        aliases = []

    if result_of_parsing.pathToSingleMail is not None:
        path_to_mail = pathlib.Path(result_of_parsing.pathToSingleMail)
        try:
            path_to_mail.resolve()
        except FileNotFoundError:
            print("File not found")
            sys.exit(1)
        if not path_to_mail.is_file():
            print("Not a file")
            sys.exit(1)
        try:
            parser = letterparser.LetterParser(str(path_to_mail))
            parser.parse_lines(iterate_file(str(path_to_mail)))
            mails = list(map(lambda x: mimemail.Mail(aliases, login, *x),
                             parser.get_letter_attributes()))
            print("x")
        except letterparser.MailParsingException as e:
            print("'{}' failed with error : '{}'".format(path_to_mail, str(e)))
            sys.exit(1)
    else:
        mails = []
        path_to_folder = pathlib.Path(result_of_parsing.pathToFolderWithMails)
        try:
            path_to_folder.resolve()
        except FileNotFoundError:
            print("Folder not found")
            sys.exit(1)
        if not path_to_folder.is_dir():
            print("Not a folder")
            sys.exit(1)
        for path in path_to_folder.iterdir():
            if path.is_dir():
                continue
            if path.suffix != '.lttr':
                continue
            try:
                parser = letterparser.LetterParser(str(path))
                parser.parse_lines(str(path))
                mails_to_append = list(map(lambda x: mimemail.Mail(aliases,
                                                                   login, *x),
                                           parser.get_letter_attributes()))
            except letterparser.MailParsingException as e:
                print("'{}' failed with error : '{}'".format(path, str(e)))
            else:
                for mail in mails_to_append:
                    mails.append(mail)
    y = smtp.SMTP(server, port, login,
                  password, result_of_parsing.debug)
    was_interrupted, delivery_results = y.send(mails)
    for result in delivery_results:
        print(result)
    if was_interrupted:
        sys.exit(1)


if __name__ == '__main__':
    main()
