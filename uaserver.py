#!/usr/bin/python3
# -*- coding: utf-8 -*-

import uaclient
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import sys
import socketserver
import os
import json


class UaServer(ContentHandler):

    def __init__(self):
        """
        Constantes que declaramos.
        """
        self.log = ""
        self.sport = ""
        self.sip = ""
        self.uaname = ""
        self.rtpport = ""
        self.f_audio = ""

    def startElement(self, name, attrs):
        """
        Método que lee etiquetas y guarda el atributo del documento xml.
        """
        if name == 'log':
            self.log = attrs.get('path', "")
        elif name == 'uaserver':
            self.sip = attrs.get('ip', "")
            self.sport = attrs.get('puerto', "")
        elif name == 'account':
            self.uaname = attrs.get('username', "")
        elif name == 'rtpaudio':
            self.rtpport = attrs.get('puerto', "")
        elif name == 'regproxy':
            self.prip = attrs.get('ip', "")
            self.prport = attrs.get('puerto', "")
        elif name == 'audio':
            self.f_audio = attrs.get('path', "")

    def Return(self):
        return(self.sip, self.log, self.sport, self.uaname, self.rtpport,
               self.prip, self.prport, self.f_audio)


class EchoHandler(socketserver.DatagramRequestHandler):

    def handle(self):
        defclient = uaclient.UaClient()
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
        if self.sip == '':
            self.sip = '127.0.0.1'
        self.uaname = Ldata[3]
        self.rtpport = Ldata[4]
        self.prip = Ldata[5]
        self.prport = Ldata[6]
        self.f_audio = Ldata[7]

        lines = []
        for line in self.rfile:

            if not line or line.decode('utf-8') != '\r\n':
                line = line.decode('utf-8')
                print(line)
                lines.append(line)

        if 'INVITE'in lines[0]:

            data = []
            p_log = 'Received from ' + self.prip + (':') + str(self.prport)
            p_log += (' ') + lines[0].replace('\r\n', ' ')
            defclient.Date((p_log), self.log)

            self.wfile.write(b"SIP/2.0 100 Trying\r\n\r\n")
            self.wfile.write(b"SIP/2.0 180 Ringing\r\n\r\n")

            line = "SIP/2.0 200 OK\r\n"
            line += 'Content-Type: application/sdp' + '\r\n\r\n'
            line += 'v=0\r\n' + 'o=' + self.uaname + ' ' + self.sip + '\r\n'
            line += 's=hola\r\n' + 't=0\r\n'
            line += 'm=audio ' + self.rtpport + ' RTP\r\n\r\n'
            self.wfile.write(bytes(line, 'utf-8'))

            l_log = 'Sent to ' + self.prip + (':') + self.prport + (' ')
            l_log += "SIP/2.0 100 Trying " + "SIP/2.0 180 Ringing "
            l_log += line.replace('\r\n', ' ')
            defclient.Date((l_log), self.log)

            ipclient = lines[3][lines[3].rfind(' ')+1:]
            ipclient = ipclient[:ipclient.rfind('\r\n')]
            portclient = lines[6][lines[6].find(' ')+1:]
            portclient = portclient[:portclient.rfind(' ')]
            data = {}
            data[portclient] = ipclient

            with open('invited.json', 'w') as outfile:
                json.dump(data, outfile, separators=(',', ':'), indent="")

        elif 'ACK' in lines[0]:
            p_log = 'Received from ' + self.prip + (':') + str(self.prport)
            p_log += (' ') + lines[0].replace('\r\n', ' ')
            defclient.Date((p_log), self.log)

            if os.path.exists('invited.json'):
                with open('invited.json') as data_file:
                    data = json.load(data_file)

            for clave, valor in data.items():
                port = clave
                ip = valor

            f_audio = self.f_audio[self.f_audio.rfind('/')+1:]
            # ENVIO RTP
            defclient.SendRTP(ip, port, f_audio)

            l_log = 'Sent to ' + ip + (':') + port + (' ')
            l_log += "RTP"
            defclient.Date((l_log), self.log)

        elif 'BYE' in lines[0]:
            p_log = 'Received from ' + self.prip + (':') + str(self.prport)
            p_log += (' ') + lines[0].replace('\r\n', ' ')
            defclient.Date((p_log), self.log)

            line = "SIP/2.0 200 OK\r\n\r\n"
            self.wfile.write(bytes(line, 'utf-8'))

            l_log = 'Sent to ' + self.prip + (':') + self.prport + (' ')
            l_log += line.replace('\r\n', ' ')
            defclient.Date((l_log), self.log)

        else:
            line = 'SIP/2.0 405 Method Not Allowed\r\n\r\n'
            self.wfile.write(bytes(line, 'utf-8'))

if __name__ == "__main__":

    parser = make_parser()
    server = UaServer()
    parser.setContentHandler(server)
    defclient = uaclient.UaClient()
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
    LOG = Data[1]
    serv = socketserver.UDPServer((IP, int(PORT)), EchoHandler)
    print("Listening...")
    defclient.Date(('Starting...'), LOG)
    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        print("Finalizado servidor")
        defclient.Date(('Finishing...'), LOG)
