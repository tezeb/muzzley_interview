#!/usr/bin/env python

import socket

def cmp(t1, t2):
    if t1 == t2:
        print("[+] OK")
    else:
        print("[-] FAIL:\t", repr(t1), " != ", repr(t2))

def runner(request, headers=[], content=""):
    ip = "127.0.0.1"
    port = 1234
    d = b"\r\n"
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((ip, port))
        sock.send(request.encode('ascii'))
        sock.send(d)
        for h in headers:
            sock.send(h.encode('ascii'))
            sock.send(d)
        sock.send(d)
        sock.send(content.encode('ascii'))
        return sock.recv(4096).decode('ascii')

def test1():
    ret = runner("GET / HTTP/1.1")
    cmp(ret, "HTTP/1.1 200 OK\r\n\r\n")

if __name__ == "__main__":
    test1()
