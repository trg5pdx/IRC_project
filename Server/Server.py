# Made by Thomas Gardner, 2022
# Using the HTTP server code from the books coding problems to help with
# starting the server code

from socket import *
import sys
import threading

# Following the stackoverflow post below for handling multiple connections
# https://stackoverflow.com/questions/61911301/handling-multiple-connections-in-python-with-sockets

# Also using this to help with communicating the message between threads
# https://stackoverflow.com/questions/51242467/communicate-data-between-threads-in-python

queue = []
lock = threading.Condition()

def handler(client_socket):
    print("ping")
    response = ""
    while response != "/quit":
        if len(queue) > 0:
            for i in queue:
                i = i + "\n"
                client_socket.send(i.encode())
        response = client_socket.recv(1024).decode()
        print(response)
        lock.acquire()
        print("lock acquired")
        queue.append(response)
        client_socket.send("message received".encode())
        if response == "/quit":
            client_socket.send("disconnecting...".encode())
            client_socket.close()
        lock.release()
        print("lock freed")
        print(queue)

serverSocket = socket(AF_INET, SOCK_STREAM)

serverPort = 45876 
serverSocket.bind(('', serverPort))
serverSocket.listen(1)

print("Ready to accept connections\n")

while True:
    connectionSocket, addr = serverSocket.accept()
    threading.Thread(target=handler, args=(connectionSocket,), daemon=True).start() 
