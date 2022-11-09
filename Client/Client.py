# Made by Thomas Gardner, 2022
# Using the TCP client example from the book to get set up

from socket import *
import sys
import threading
import readline

def receive_server_responses(client_socket):
    while True:
        message = client_socket.recv(1024).decode()
        print(message)


def main():
    client_socket = socket(AF_INET, SOCK_STREAM)
    server_name = 'localhost'
    server_port = 45876 
        
    if len(sys.argv) > 1 and len(sys.argv) < 4:
        server_host = sys.argv[1]
        server_port = int(sys.argv[2])
        print("server host and port set at commandline")

    client_socket.connect((server_name, server_port))
    
    threading.Thread(target=receive_server_responses, args=(client_socket,), daemon=True).start()

    message = "" 
    while message != "/quit":
        message = input("Enter your message:\n")
        client_socket.send(message.encode())

    client_socket.close()
    sys.exit()

if __name__ == '__main__':
    main()
