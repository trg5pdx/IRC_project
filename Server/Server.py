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
    with client_socket:
        while response != "/quit":
            if len(queue) > 0:
                for i in queue:
                    i = i + "\n"
                    client_socket.send(i.encode())
            response = client_socket.recv(1024).decode()

            if response == "/quit":
                client_socket.send("disconnecting...".encode())
                client_socket.close()
            else:
                lock.acquire()
                print(response)
                print("lock acquired")
                queue.append(response)
                client_socket.send("message received".encode())
                lock.release()
                print("lock freed")

def accept_connections(server_socket):
    while True:
        connection_socket, addr = server_socket.accept()
        threading.Thread(target=handler, args=(connection_socket,), daemon=True).start() 

def print_help():
    print("/help: prints this menu")
    print("/history: prints out the current message history")
    print("/quit: closes the server")

def main():
    server_socket = socket(AF_INET, SOCK_STREAM)

    server_port = 45876 
    server_host = 'localhost'
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
