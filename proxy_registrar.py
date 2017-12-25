#!/usr/bin/python3
# -*- coding: utf-8 -*-


from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import sys
import socketserver
import os.path


class Constants(ContentHandler):
    """
    Constantes que se leeran del documento xml.
    IP, PUERTO Y NPMBRE DEL PROXY-REGISTRAR.
    """

    def __init__(self):
        self.prip = ""
        self.prport = ""
        self.namepr = ""

    def startElement(self, name, attrs):
        if name == 'server':
            self.prip = attrs.get('ip', "")
            self.prport = attrs.get('puerto', "")
            self.namepr = attrs.get('name', "")

    def PrReg(self):
        return (self.prip, self.prport, self.namepr)


class Proxy_Registrar(socketserver.DatagramRequestHandler):

    def handle(self):
        """
        Parte servidora
        """
        # Coge las variables del xml llamando a la clase Constants,
        # para poder utilizarlas en esta clase.
        parser = make_parser()
        cts = Constants()
        parser.setContentHandler(cts)
        dproxy = sys.argv[1]
        parser.parse(open(dproxy))

        Ldata = cts.PrReg()
        self.prip = Ldata[0]
        self.prport = Ldata[1]

        # Parte de función servidora.
        lines = []
        for line in self.rfile:
            if not line or line.decode('utf-8') != '\r\n':
                line = line.decode('utf-8')
                print(line)
                lines.append(line)

        METHOD = (lines[0][:lines[0].find(' ')])
        if METHOD == 'REGISTER' and len(lines) == 2:
            message = 'SIP/2.0 401 Unauthorized\r\n'
            message += 'WWW Authenticated: Digest nonce="898989"\r\n\r\n'
            self.wfile.write(bytes(message, 'utf-8'))

        elif METHOD == 'REGISTER' and len(lines) == 3:
            self.wfile.write(b"SIP/2.0 200 OK\r\n\r\n")

if __name__ == "__main__":
    """
    Programa principal
    """
    # Vuelve a coger el valor de las variables de la clase Constants.

    parser = make_parser()
    cts = Constants()
    parser.setContentHandler(cts)
    try:
        dproxy = sys.argv[1]
    except IndexError:
        sys.exit('Usage: python proxy_registrar.py config')
    try:
        parser.parse(open(dproxy))
    except FileNotFoundError:
        sys.exit('Usage: python proxy_registrar.py config')

    Ldata = cts.PrReg()
    IP = repr(Ldata[0])
    IP = IP[:IP.rfind("'")]
    IP = IP[IP.find("'")+1:]
    NAME = Ldata[2]

    # Parte servidora que cogemos de la clase Proxy_Registrar
    serv = socketserver.UDPServer((str(IP), int(Ldata[1])), Proxy_Registrar)

    print("Server " + NAME + " listening at port " + Ldata[1] + ("..."))
    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        print("Finalizado servidor")
