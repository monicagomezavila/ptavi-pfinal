#!/usr/bin/python3
# -*- coding: utf-8 -*-


from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import sys
import socketserver
import os.path
import time
import json
import uaclient


class Constants(ContentHandler):
    """
    Constantes que se leeran del documento xml.
    IP, PUERTO Y NOMBRE DEL PROXY-REGISTRAR.
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
        if name == 'log':
            self.logpath = attrs.get('path', "")

    def PrReg(self):
        return (self.prip, self.prport, self.namepr, self.logpath)


class Proxy_Registrar(socketserver.DatagramRequestHandler):

    def JsonExists(self):
        """
        Si existe un json lo abre y lo lee y lo añade al diccionario
        Si no existe pone el diccionario a vacio
        """
        if os.path.exists('passwds.json'):
            with open('passwds.json') as data_file:
                data = json.load(data_file)
            self.dicc_ua = data
        else:
            self.dicc_ua = {}

    def UsersJson(self, fichjson='passwds.json'):
        """
        Crea con el diccionario un json
        """
        with open(fichjson, 'w') as outfile:
            json.dump(self.dicc_ua, outfile, separators=(',', ':'), indent="")

    def UserCaducado(self):
        n = 1
        while n <= len(self.dicc_ua):
            for user in self.dicc_ua:
                now = time.time()
                if self.dicc_ua[user][3] <= now:
                    del self.dicc_ua[user]
                    break
            n = n+1

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
        self.logpath = Ldata[3]

        # Parte de función servidora.
        self.JsonExists()
        self.UserCaducado()
        defclient = uaclient.UaClient()
        lines = []

        for line in self.rfile:

            if not line or line.decode('utf-8') != '\r\n':
                line = line.decode('utf-8')
                print(line)
                lines.append(line)

        # Si el metodo es REGISTER hay dos opciones // nonce
        METHOD = (lines[0][:lines[0].find(' ')])
        ipport_client = list(self.client_address)
        ipclient = ipport_client[0]

        if METHOD == 'REGISTER' and len(lines) == 2:
            l_log = 'Received from ' + ipclient + (':') + str(ipport_client[1])
            l_log += (' ') + lines[0].replace('\r\n', ' ')
            defclient.Date((l_log), self.logpath)

            defclient.Date((l_log), self.logpath)
            message = 'SIP/2.0 401 Unauthorized\r\n'
            message += 'WWW Authenticated: Digest nonce="898989"\r\n\r\n'
            self.wfile.write(bytes(message, 'utf-8'))

            l_log = 'Sent to ' + ipclient + (':') + str(ipport_client[1])
            l_log += (' ') + message.replace('\r\n', ' ')
            defclient.Date((l_log), self.logpath)

        elif METHOD == 'REGISTER' and len(lines) == 3:
            self.wfile.write(b"SIP/2.0 200 OK\r\n\r\n")
            l_log = 'Sent to ' + ipclient + (':') + str(ipport_client[1])
            message = "SIP/2.0 200 OK\r\n\r\n"
            l_log += (' ') + message.replace('\r\n', ' ')
            defclient.Date((l_log), self.logpath)

            expiresua = lines[1][lines[1].rfind(' ')+1:]
            sport = lines[0][lines[0].rfind(':')+1:]
            sport = sport[:sport.rfind(' ')]
            timeinsec = time.time()
            expirationua = timeinsec + int(expiresua)
            uaname = lines[0][lines[0].find(':')+1:]
            uaname = uaname[:uaname.find(':')]

            # Mira el valor de expires y en funcion de el hace
            if int(expiresua) > 0:
                list_ua = [ipclient, sport, timeinsec, expirationua]
                self.dicc_ua[uaname] = list_ua
            elif int(expiresua) == 0:
                if uaname in self.dicc_ua:
                    del self.dicc_ua[uaname]

        elif METHOD == 'INVITE':
            uainvited = lines[0][lines[0].rfind(':')+1:]
            uainvited = uainvited[:uainvited.find(' ')]
            message = ""
            if uainvited in self.dicc_ua:
                print('----SE ENVIARÍA AL OTRO USER')
                for line in lines:
                    message += line
                message = message + '\r\n'
            else:
                message = 'SIP/2.0 404 User Not Found\r\n\r\n'
                self.wfile.write(bytes(message, 'utf-8'))
                l_log = 'Sent to ' + ipclient + (':')
                l_log += str(ipport_client[1]) + (' ')
                l_log += message.replace('\r\n', ' ')
                defclient.Date((l_log), self.logpath)
        self.UsersJson()

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
    LOG = Ldata[3]

    # Parte servidora que cogemos de la clase Proxy_Registrar
    serv = socketserver.UDPServer((str(IP), int(Ldata[1])), Proxy_Registrar)

    print("Server " + NAME + " listening at port " + Ldata[1] + ("..."))
    defclient = uaclient.UaClient()
    defclient.Date('Starting...', LOG)
    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        print("Finalizado servidor")
