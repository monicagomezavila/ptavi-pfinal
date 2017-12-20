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
        print(self.prip)
        print(self.prport)

        # Parte de función servidora.
        for line in self.rfile:
            if line.decode('utf-8') != '\r\n' or '' or not line:
                linea = line.decode('utf-8')
                print(linea)


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
        sys.exit('Usage: python uaclient.py config method option')
    try:
        parser.parse(open(dproxy))
    except FileNotFoundError:
        sys.exit('Usage: python uaclient.py config method option')

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
