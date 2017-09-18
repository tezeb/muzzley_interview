#!/usr/bin/env python

import socket
from time import sleep
import random
from base64 import b64encode
from hashlib import sha1
from binascii import unhexlify
from websocket import create_connection

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
            if content != "":
                sock.send(content.encode('ascii'))
            while ret.find(d + d) == -1:
               ret.extend(sock.recv(4096)) 
    except BrokenPipeError as e:
        print('[-]',e)
    hend = ret.find(b'\r\n\r\n')
    hdrs = ret
    content = ""
    if hend != -1:
        hdrs = ret[:hend].decode('ascii').split('\r\n')
        content = ret[hend+4:]
    return (hdrs, content)

def test(req, exp, headers=[], content=b""):
    hdr, cont = runner(req, headers=headers)
    for i in exp:
        if i not in hdr:
            print("[-] FAIL(header):",repr(i),"not found")
            for j in hdr:
                print("\t[>]",repr(j))
            return False
    if content != b"" and cont != content:
        print("[-] FAIL(body):",repr(content),"not found")
    print("[+] OK")
    #   delay test execution to allow server to relisten
    #   as it handles single connection only
    sleep(.01)
    return True

def test1():
    ws = create_connection("ws://127.0.0.1:1234/ws")
    t = ws.recv() 
    if t == "{\"status\":\"success\"}":
        print("[+] OK")
    else:
        print("[-] FAIL: Invalid data:", repr(t))
    ws.close()


def getWSKey():
    wsKeyConst = b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
    key = b64encode(unhexlify(hex(random.getrandbits(16*8))[2:].rjust(32, '0')))
    return (key.decode('ascii'), b64encode(sha1(key + wsKeyConst).digest()).decode('ascii'))

if __name__ == "__main__":
    test("GET / HTTP/1.1", ["HTTP/1.1 404 Not Found"])
    test("GET /something HTTP/1.1", ["HTTP/1.1 404 Not Found"])
    test("GET  HTTP/1.1", ["HTTP/1.1 400 Bad Request"])
    #   RFC example
    test("GET /ws HTTP/1.1", [
            "HTTP/1.1 101 Switching Protocols",
            "Upgrade: websocket",
            "Connection: Upgrade",
            "Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo="
            ],
            headers = [
                "Host: example.com",
                "Upgrade: websocket",
                "Connection: Upgrade",
                "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ=="
                ],
            content=b"\x81\x14{\"status\":\"success\"}\x88\x00"
        )
    for i in range(5):
        wskey = getWSKey()
        test("GET /ws HTTP/1.1", [
                "HTTP/1.1 101 Switching Protocols",
                "Upgrade: websocket",
                "Connection: Upgrade",
                "Sec-WebSocket-Accept: " + wskey[1],
                ],
                headers = [
                    "Host: example.com",
                    "Upgrade: websocket",
                    "Connection: Upgrade",
                    "Sec-WebSocket-Key: " + wskey[0],
                    ]
            )
    test1()
