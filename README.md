# SMTP client

*Note: this client only works in ESMTP ssl encrypted mode*

### Keys

* `-d` - turn on debug mode

* `-s` - takes path to mail (see 'Mail format' section) as an argument
and sends it

**OR**

* `-m` - takes path to folder with mails as an argument

### Login and password

Server, port, login and password are stored in first four lines of
`userinfo.usinf` file correspondingly

### Aliases

Aliases are stored in optional file `aliases.json`

Format of this file:

    thisisfirstalias:thisisfirstsubstitute;
    thisisSECONDalias:THISISsEcOnDsubstitute;

You can use those aliases in your letter surrounded by %'s

For example: "%thisisfirstalias%, hi there!"
Will be shown like: "thisisfirstsubstitute, hi there!"

### Mail format

Mail - is a simple UTF-8 text file with "*.lttr" name and with following formatting and order:

    to: aaaa@gmail.com, bbb@yahoo.com
    type: plain
    subject: Waddup
    attachment: /bin/bash
    Hi there! This is the text of the message

You can omit 'attachment' tag(s) if you don't want to attach any files to your
 letter, but the other tags ('to', 'type, 'subject') are required
'to' support several emails. Just put a couple of emails separated by ' ' or ', ' and it will work!
'type' takes either 'plain' or 'html' as an argument
