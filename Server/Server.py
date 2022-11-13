# Made by Thomas Gardner, 2022
# Using the HTTP server code from the books coding problems to help with
# starting the server code

from socket import *
import sys
import threading
from Connections import *
from Chat import *

# Following the stackoverflow post below for handling multiple connections
# https://stackoverflow.com/questions/61911301/handling-multiple-connections-in-python-with-sockets

# Also using this to help with communicating the message between threads
# https://stackoverflow.com/questions/51242467/communicate-data-between-threads-in-python

queue = []
lock = threading.Condition()

def accept_connections(server_socket, server_chatrooms):
    while True:
        connection_socket, addr = server_socket.accept()
        initial_client_command = connection_socket.recv(1024).decode()
        command = initial_client_command.split()
        # Come back and add error handling for when a client would send the wrong command
        name = command[1]
        name_ack = "Welcome " + name + " to the IRC server!\n"
        connection_socket.send(name_ack.encode()) 

        client = connections(name, connection_socket)
        # client.send_message_history(queue)
        threading.Thread(target=client.send_new_messages, args=(server_chatrooms,), daemon=True).start() 
        threading.Thread(target=client.receive_message, args=(server_chatrooms, lock,), daemon=True).start() 

def print_help():
    return """
/help: prints this menu
/history: prints out the current message history
/create <name>: creates a chatroom with the specified name
/listcr: lists the currently open chatrooms
/joincr <name>: join the chatroom with the specified name
/leavecr <name>: leave the chatroom with the specified name
/quit: closes the server"""

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

    server_chatrooms = []

    print("Ready to accept connections\n")
    # Spinning up another thread to allow for it to accept connections and have the
    # server be able to run commands on it's own
    threading.Thread(target=accept_connections, args=(server_socket, server_chatrooms,), daemon=True).start()
    
    server_command = ""

    while server_command != "/quit":
        server_command = input()
        given_command = server_command.split()

        match given_command[0]:
            case "/help":
                print(print_help())
            case "/history":
                print(queue)
            case "/create":
                if len(given_command) > 1:
                    name = given_command[1]
                    add_new_room(server_chatrooms, lock, name)
            case "/listcr":
                chatlist = list_rooms(server_chatrooms)
                print("List of currently open chatrooms:\n")
                print(chatlist)
            case "/listme":
                if len(given_command) > 1:
                    current_room = given_command[1]
                    user_list = list_connected_users(server_chatrooms, current_room)
                    print(user_list)
            case "/quit":
                print("closing server...")
            case other:
                print("Unknown command")

if __name__ == '__main__':
    main()
