#!/usr/bin/env python3

import socket

HOST = "127.0.0.1"
PORT = 5555

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server.bind((HOST, PORT))
server.listen(1)

print(f"EOS Collector listening on {HOST}:{PORT}")

while True:
    conn, addr = server.accept()
    print(f"Connected: {addr}")

    while True:
        data = conn.recv(4096)

        if not data:
            print("Client disconnected")
            break

        print(f"Received ({len(data)} bytes):")
        print(data)
        print(data.decode(errors="replace"))

    conn.close()
