#!/usr/bin/env python3

import os
import socket

class HTTPSinleRequestServer:

    def __init__(self):
        self.d = b'\r\n'
        self.msgs = {
                101: b"101 Switching Protocols",
                200: b"200 OK",
                400: b"400 Bad Request",
                404: b"404 Not Found",
                501: b"501 Not Implemented",
                }
        self.prot = b"HTTP/1.1 "

    def listen(self, ip, port):
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
        conn.send(self.prot)
        conn.send(self.msgs[code])
        conn.send(self.d)
        for h in headers:
            conn.send(h.encode('ascii'))
            conn.send(self.d)
        conn.send(self.d)
        if content != "":
            conn.send(content.encode('ascii'))
        if close:
            conn.close()
    
    def handle(self, conn):
        headers = bytearray()
        fl = False
        while True:
            data = conn.recv(4096)
            if not fl:
                hend = data.find(self.d)
                if hend != -1:
                    headers.extend(data[:hend])
                else:
                    headers.extend(data)
            if data.find(self.d + self.d):
                break

        print("[>]", repr(headers))

        req = headers.decode('ascii').split(' ') 
        head = False

        if req[0] == "GET":
            pass
        elif req[0] == "HEAD":
            head = True
        else:
            self.respond(conn, 501) 
            return

        if req[2] != 'HTTP/1.0' and req[2] != 'HTTP/1.1': 
            self.respond(conn, 400)
            return

        if req[1] == "":
            self.respond(conn, 400)
            return
        elif req[1] != '/ws':
            self.respond(conn, 404)
            return

        if head:
            self.respond(conn, 400)

        #   TODO:
        sec_accept_value = ""

        self.respond(conn, 101, headers = [
            "Upgrade: websocket",
            "Connection: Upgrade",
            "Sec-WebSocket-Accept: " + sec_accept_value
            ],
            content='{"status":"success"}'
            )

def main():
    #   TODO: use args
    ip = "127.0.0.1"
    port = 1234
    while True:
        try:
            s = HTTPSinleRequestServer()
            s.listen(ip, port)
        except Exception as e:
            #print("[!]",e)
            raise

if __name__ == "__main__":
    main()
