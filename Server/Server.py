# Made by Thomas Gardner, 2022
# Using the HTTP server code from the books coding problems to help with
# starting the server code

from socket import *
import sys

serverSocket = socket(AF_INET, SOCK_STREAM)

serverPort = 45876 
serverSocket.bind(('', serverPort))
serverSocket.listen(1)

print("Ready to accept connections\n")
connectionSocket, addr = serverSocket.accept()
message = ""

while message != "/quit":
    response = connectionSocket.recv(1024).decode()
    print(response)
    message = input("Enter your response:\n")
    connectionSocket.send(message.encode()) 
    if message == "/quit":
        connectionSocket.send("Connection shutting off...\n".encode())
        serverSocket.close()

sys.exit()
