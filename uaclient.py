#!/usr/bin/python3
# -*- coding: utf-8 -*-

from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import sys
import os.path
import time


class UaClient(ContentHandler):
    """
    Clase para manejar clientes
    """
    def __init__(self):
        """
        Variables que obtendremos del documento XML
        """
        self.prip = ""
        self.prport = ""
        self.uaname = ""
        self.sport = ""
        self.rtpip = ""
        self.logpath = ""

    def startElement(self, name, attrs):
        """
        Método que lee etiquetas y guarda su valor
        """
        if name == 'regproxy':
            self.prip = attrs.get('ip', "")
            self.prport = attrs.get('puerto', "")
        elif name == 'account':
            self.uaname = attrs.get('username', "")
        elif name == 'uaserver':
            self.sport = attrs.get('puerto', "")
            self.sip = attrs.get('ip', "")
        elif name == 'rtpaudio':
            self.rtpport = attrs.get('puerto', "")
        elif name == 'log':
            logpath = attrs.get('path', "")
            self.log = logpath[logpath.rfind('/')+1:]

    def Date(self, line):
        if os.path.exists(self.log):
            l_date = (list(time.localtime(time.time()))[:6])
            date = ""
            for element in l_date:
                date = date + str(element)
            date = date + (' ') + line + ('\n')
            with open(self.log, 'a') as outfile:
                outfile.write(date)

    def Method(self):
        """
        Parte de cliente. Se registra, manda invite, bye
        """
        if len(sys.argv) != 4:
            sys.exit('Usage: python uaclient.py config method option')

        if sys.argv[2] == 'REGISTER':
            line = 'REGISTER sip:' + self.uaname + ':'
            line += self.sport + ' SIP/2.0\r\n'
            line += 'Expires: ' + sys.argv[3] + '\r\n\r\n'
        elif sys.argv[2] == 'INVITE':
            line = 'INVITE sip:' + sys.argv[3] + ' SIP/2.0\r\n'
            line += 'Content-Type: application/sdp' + '\r\n\r\n'
            line += 'v=0\r\n' + 'o=' + self.uaname + ' ' + self.sip + '\r\n'
            line += 's=misesion\r\n' + 't=0\r\n'
            line += 'm=audio ' + self.rtpport + ' RTP\r\n\r\n'
        elif sys.argv[2] == 'BYE':
            line = 'BYE sip:' + sys.argv[3] + ' SIP/2.0\r\n\r\n'
        else:
            print('Usage: python uaclient.py config method option')

        print(line)

if __name__ == "__main__":
    """
    Programa principal
    """
    parser = make_parser()
    client = UaClient()
    parser.setContentHandler(client)
    duser = sys.argv[1]

    try:
        parser.parse(open(duser))
    except FileNotFoundError:
        sys.exit('Usage: python uaclient.py config method option')
    client.Method()
    client.Date('hey')
