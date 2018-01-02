#!/usr/bin/python3
# -*- coding: utf-8 -*-

from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import sys
import os
import os.path
import time
import socket


class UaClient(ContentHandler):
    """
    Clase para manejar clientes
    """
    def __init__(self):
        """
        Constantes que declaramos.
        """
        self.prip = ""
        self.prport = ""
        self.uaname = ""
        self.sport = ""
        self.logpath = ""
        self.sip = ""
        self.uapasswd = ""

    def startElement(self, name, attrs):
        """
        Método que lee etiquetas y guarda el atributo del documento xml.
        """
        if name == 'regproxy':
            self.prip = attrs.get('ip', "")
            self.prport = attrs.get('puerto', "")
        elif name == 'account':
            self.uaname = attrs.get('username', "")
            self.uapasswd = attrs.get('passwd', "")
        elif name == 'uaserver':
            self.sport = attrs.get('puerto', "")
            self.sip = attrs.get('ip', "")
        elif name == 'rtpaudio':
            self.rtpport = attrs.get('puerto', "")
        elif name == 'log':
            self.logpath = attrs.get('path', "")

    def Date(self, line, path):
        """
        Da la fecha del momento en el que se llama a la funcion.
        Escribe en el fichero log.
        """
        if os.path.exists(path):
            l_date = (list(time.localtime(time.time()))[:6])
            date = ""
            for element in l_date:
                date = date + str(element)
            date = date + (' ') + line + ('\n')
            with open(path, 'a') as outfile:
                outfile.write(date)

    def Method(self):
        """
        Parte de cliente. Se registra, manda invite, bye.
        """
        if len(sys.argv) != 4:
            sys.exit('Usage: python uaclient.py config method option')

        UaClient().Date('Starting...', self.logpath)

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
            sys.exit('Usage: python uaclient.py config method option')

        l_log = 'Sent to ' + self.prip + ':' + self.prport + (': ')
        l_log += line[:line.rfind('\r\n\r\n')]
        l_log = l_log.replace('\r\n', ' ')
        UaClient().Date(l_log, self.logpath)

        """
        Creamos el socket, lo configuramos y lo atamos a un servidor/puerto.
        """
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
            my_socket.connect((str(self.prip), int(self.prport)))
            my_socket.send(bytes(line, 'utf-8') + b'\r\n')
            try:
                data = my_socket.recv(1024)
                print(data.decode('utf-8'))
            except ConnectionRefusedError:
                error = 'Error: No server listening at ' + self.prip
                error = error + ' port ' + self.prport
                UaClient().Date(error, self.logpath)
                sys.exit(error)

            l_log = 'Reviced from ' + self.prip + ':' + self.prport + (': ')
            recived = data.decode('utf-8')
            l_log += recived[:recived.rfind('\r\n\r\n')]
            l_log = l_log.replace('\r\n', ' ')
            UaClient().Date(l_log, self.logpath)

            message_proxy = (data.decode('utf-8').split())
            if '401' in message_proxy:
                line = 'REGISTER sip:' + self.uaname + ':'
                line += self.sport + ' SIP/2.0\r\n'
                line += 'Expires: ' + sys.argv[3] + '\r\n'
                line += 'Authorization: Digest response="'
                line += self.uapasswd + ('"\r\n')
                my_socket.send(bytes(line, 'utf-8') + b'\r\n')

                l_log = 'Sent to ' + self.prip + ':' + self.prport + (': ')
                l_log += line[:line.rfind('\r\n\r\n')]
                l_log = l_log.replace('\r\n', ' ')
                UaClient().Date(l_log, self.logpath)

                data = my_socket.recv(1024)
                data = data.decode('utf-8')
                print(data)
                l_log = 'Reviced from ' + self.prip + ':' + self.prport
                l_log += (': ') + data.replace('\r\n', ' ')
                UaClient().Date(l_log, self.logpath)

            if ('Trying' and 'Ringing'and 'OK') in message_proxy:
                origin = message_proxy[12][message_proxy[12].find('=')+1:]
                line = 'ACK sip:' + origin + (' SIP/2.0\r\n\r\n')
                my_socket.send(bytes(line, 'utf-8') + b'\r\n')

                l_log = 'Sent to ' + self.prip + ':' + self.prport + (': ')
                l_log += line[:line.rfind('\r\n\r\n')]
                l_log = l_log.replace('\r\n', ' ')
                UaClient().Date(l_log, self.logpath)

if __name__ == "__main__":
    """
    Programa principal
    """
    # Coge las constantes de la clase UaClient
    parser = make_parser()
    client = UaClient()
    parser.setContentHandler(client)
    duser = sys.argv[1]

    try:
        parser.parse(open(duser))
    except FileNotFoundError:
        sys.exit('Usage: python uaclient.py config method option')
    client.Method()
