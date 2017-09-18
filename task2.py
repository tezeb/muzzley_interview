#!/usr/bin/env python3

import os
import socket
from base64 import b64encode
from hashlib import sha1
from struct import pack

class HTTPSinleRequestServer:
    DELIM = b'\r\n'
    MSGS = {
            101: b"101 Switching Protocols",
            200: b"200 OK",
            400: b"400 Bad Request",
            404: b"404 Not Found",
            501: b"501 Not Implemented",
            }
    PROT = b"HTTP/1.1 "
    WS_GUID_CONST = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

    def __init__(self, ip, port):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.bind((ip, port))
                sock.listen()
                conn, addr = sock.accept()
                sock.shutdown(socket.SHUT_RDWR)
                print("[+] New connection:", addr)
                self.handle(conn)
        except OSError as err:
            print("[-]", err)

    def respond(self, conn, code, headers=[], content="", close=True):
        conn.send(self.PROT)
        conn.send(self.MSGS[code])
        conn.send(self.DELIM)
        for h in headers:
            conn.send(h.encode('ascii'))
            conn.send(self.DELIM)
        conn.send(self.DELIM)
        if content != "":
            conn.send(content)
        if close:
            conn.close()

    def validateWSRequest(self, request, headers):
        req = request.split(' ') 
        head = False

        if req[0] == "GET":
            pass
        elif req[0] == "HEAD":
            return (False,400)
        else:
            return (False,501) 
            return

        if req[2] != 'HTTP/1.1': 
            return (False,400)

        if req[1] == "":
            return (False,400)
        elif req[1] != '/ws':
            return (False,404)

        return (True, 101)
    
    def handle(self, conn):
        headers = bytearray()
        while True:
            headers.extend(conn.recv(4096))
            hend = headers.find(self.DELIM + self.DELIM)
            if hend != -1:
                headers = headers[:hend]
                break

        headers = headers.decode('ascii').split(self.DELIM.decode('ascii'))
        if len(headers) == 0:
            #   probably throw here - connection ended without data
            conn.close()
            return

        request = headers.pop(0)
        headers = dict(t.split(':') for t in headers)

        print("[>]", repr(request))

        (valid, code) = self.validateWSRequest(request, headers)

        if not valid:
            self.respond(conn, code)
            return

        print("[>]", repr(headers["Sec-WebSocket-Key"]))

        concat = headers["Sec-WebSocket-Key"].strip() + self.WS_GUID_CONST
        sec_accept_value = b64encode(sha1(concat.encode('ascii')).digest()).decode('ascii')

        payload=b'{"status":"success"}'
        assert(len(payload) < 126)
        wsFramedData = b"\x81" + pack('b', len(payload)) + payload
        wsCloseFrame = b"\x88\x00"

        self.respond(conn, code, headers = [
            "Upgrade: websocket",
            "Connection: Upgrade",
            "Sec-WebSocket-Accept: " + sec_accept_value
            ],
            content = wsFramedData + wsCloseFrame
            )

def main():
    #   TODO: use args
    ip = "127.0.0.1"
    port = 1234
    while True:
        try:
            HTTPSinleRequestServer(ip, port)
        except Exception as e:
            #print("[!]",e)
            raise

if __name__ == "__main__":
    main()
