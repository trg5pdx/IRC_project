# Made by Thomas Gardner, 2022
# Using the HTTP server code from the books coding problems to help with
# starting the server code

from socket import *
import sys
import threading
from Connections import *

# Following the stackoverflow post below for handling multiple connections
# https://stackoverflow.com/questions/61911301/handling-multiple-connections-in-python-with-sockets

# Also using this to help with communicating the message between threads
# https://stackoverflow.com/questions/51242467/communicate-data-between-threads-in-python

queue = []
lock = threading.Condition()

def accept_connections(server_socket):
    while True:
        connection_socket, addr = server_socket.accept()
        client = connections(connection_socket)
        client.send_message_history(queue)
        threading.Thread(target=client.send_new_messages, args=(queue,), daemon=True).start() 
        threading.Thread(target=client.receive_message, args=(queue, lock,), daemon=True).start() 

def print_help():
    print("/help: prints this menu")
    print("/history: prints out the current message history")
    print("/quit: closes the server")

def main():
    server_socket = socket(AF_INET, SOCK_STREAM)
    
    # default server host and port if none are specified
    server_host = 'localhost'
    server_port = 45876 
    
    if len(sys.argv) > 1 and len(sys.argv) < 4:
        server_host = sys.argv[1]
        server_port = int(sys.argv[2])
        print("server host and port set at commandline")

    server_socket.bind((server_host, server_port))
    server_socket.listen(1)

    print("Ready to accept connections\n")
    # Spinning up another thread to allow for it to accept connections and have the
    # server be able to run commands on it's own
    threading.Thread(target=accept_connections, args=(server_socket,), daemon=True).start()
    
    server_command = ""

    while server_command != "/quit":
        server_command = input()
        match server_command:
            case "/help":
                print_help()
            case "/history":
                print(queue)
            case "/quit":
                print("closing server...")
            case other:
                print("Unknown command")

if __name__ == '__main__':
    main()
