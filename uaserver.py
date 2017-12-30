#!/usr/bin/python3
# -*- coding: utf-8 -*-

import uaclient
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import sys
import socketserver


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
            self.log = attrs.get('path', "")
        elif name == 'uaserver':
            self.sip = attrs.get('ip', "")
            self.sport = attrs.get('puerto', "")

    def Return(self):
        return(self.sip, self.log, self.sport)

class EchoHandler(socketserver.DatagramRequestHandler):
    
    def handle(self):
        parser = make_parser()
        server = UaServer()
        parser.setContentHandler(server)
        dua = sys.argv[1]
        try:
            parser.parse(open(dua))
        except FileNotFoundError:
             sys.exit('Usage: python uaclient.py config')

        Ldata = server.Return()
        self.log = Ldata[1]
        self.sport = Ldata[2]
        self.sip = Ldata[0]

        lines =[]
        for line in self.rfile:

            if not line or line.decode('utf-8') != '\r\n':
                line = line.decode('utf-8')
                print(line)
                lines.append(line)

if __name__ == "__main__":

    parser = make_parser()
    server = UaServer()
    parser.setContentHandler(server)
    try:
        dproxy = sys.argv[1]
    except IndexError:
        sys.exit('Usage: python uaserver.py config')
    try:
        parser.parse(open(dproxy))
    except FileNotFoundError:
        sys.exit('Usage: python uaserver.py config')

    Data = server.Return()
    IP = repr(Data[0])
    IP = IP[:IP.rfind("'")]
    IP = IP[IP.find("'")+1:]
    PORT = Data[2]
    serv = socketserver.UDPServer((IP, int(PORT)), EchoHandler)
    print("Listening...")
    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        print("Finalizado servidor")
