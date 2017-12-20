#!/usr/bin/python3
# -*- coding: utf-8 -*-

import uaclient
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import sys


class UaServer(ContentHandler):

    def __init__(self):
        """
        Constantes que declaramos.
        """
        self.log = ""
        self.sport = ""
        self.sip = ""

    def startElement(self, name, attrs):
        """
        Método que lee etiquetas y guarda el atributo del documento xml.
        """
        if name == 'log':
            logpath = attrs.get('path', "")
            self.log = logpath[logpath.rfind('/')+1:]
        elif name == 'uaserver':
            self.sip = attrs.get('ip', "")
            self.sport = attrs.get('puerto', "")

    def Server(self):
        p = uaclient.UaClient()
        p.Date(('hola'), self.log)
        print(self.log)
        print(self.sip)
        print(self.sport)


if __name__ == "__main__":

    parser = make_parser()
    server = UaServer()
    parser.setContentHandler(server)
    duser = sys.argv[1]
    try:
        parser.parse(open(duser))
    except FileNotFoundError:
        sys.exit('Usage: python uaclient.py config method option')
    server.Server()
