# Made by Thomas Gardner, 2022
# Using the TCP client example from the book to get set up

from socket import *
import sys

clientSocket = socket(AF_INET, SOCK_STREAM)
serverPort = 45876 
serverName = 'localhost'
clientSocket.connect((serverName, serverPort))

message = "" 

while message != "/quit":
    message = input("Enter your message:")
    clientSocket.send(message.encode())
    response = clientSocket.recv(1024).decode()
    print(response)

clientSocket.close()
sys.exit()
