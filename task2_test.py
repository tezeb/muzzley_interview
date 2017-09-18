#!/usr/bin/env python

import socket
from time import sleep

def runner(request, headers=[], content=""):
    ip = "127.0.0.1"
    port = 1234
    d = b"\r\n"
    ret = bytearray()
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((ip, port))
            sock.send(request.encode('ascii'))
            sock.send(d)
            for h in headers:
                sock.send(h.encode('ascii'))
                sock.send(d)
            sock.send(d)
            sock.send(content.encode('ascii'))
            while ret.find(d + d) == -1:
               ret.extend(sock.recv(4096)) 
    except BrokenPipeError as e:
        print('[-]',e)
    return ret.decode('ascii').split('\r\n')

def test(req, exp):
    ret = runner(req)
    for i in exp:
        if i not in ret:
            print("[-] FAIL:",repr(i),"not found")
            for j in ret:
                print("\t[>]",repr(j))
            return False
    print("[+] OK")
    sleep(.01)
    return True

if __name__ == "__main__":
    test("GET / HTTP/1.1", ["HTTP/1.1 404 Not Found"])
    test("GET /something HTTP/1.1", ["HTTP/1.1 404 Not Found"])
    test("GET  HTTP/1.1", ["HTTP/1.1 400 Bad Request"])
    test("GET /ws HTTP/1.1", [
            "HTTP/1.1 101 Switching Protocols"
            ])
