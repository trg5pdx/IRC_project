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

lock = threading.Condition()

def accept_connections(server_socket, server_chatrooms, user_list, active):
    while True:
        connection_socket, addr = server_socket.accept()
        name = ""
        accepted_username = False
        while not accepted_username:
            initial_client_command = connection_socket.recv(1024).decode()
            command = initial_client_command.splitlines()
            if command[0] == "trgIRC/0.1 CONNCT CLIENT":
                username_line = command[1].split()
                if username_line[0] == "USERNAME":
                    name = username_line[1]
                    found_duplicate = False 
                    for user in user_list:
                        if user == name:
                            found_duplicate = True
                    if found_duplicate: 
                        name_dup = "trgIRC/0.1 CONNCT ERROR\n"
                        name_dup += "ERROR NAMEDUP\n"
                        connection_socket.send(name_dup.encode())
                    else:
                        accepted_username = True
                        lock.acquire()
                        user_list.append(name)
                        lock.release()
                        name_ack = "trgIRC/0.1 CONNCT OK\n"
                        name_ack += "MESSAGE\n"
                        name_ack += "Welcome " + name + " to the IRC server!\n\n"
                        connection_socket.send(name_ack.encode()) 
                else:
                    message = "trgIRC/0.1 CONNCT ERROR\n"
                    message += "ERROR HEADER\n"
                    connection_socket.send(message.encode())

            else:
                message = "trgIRC/0.1 CONNCT ERROR\n"
                message += "ERROR STATUS\n"
                connection_socket.send(message.encode())
        client = connections(name, connection_socket)
        threading.Thread(target=client.send_messages, args=(server_chatrooms, active,), daemon=True).start() 
        threading.Thread(target=client.receive_message, args=(server_chatrooms, lock, user_list,), daemon=True).start()

def print_help():
    return """
/help: prints this menu\n
/history: prints out the current message history\n
/create <name>: creates a chatroom with the specified name\n
/listcr: lists the currently open chatrooms\n
/joincr <name>: join the chatroom with the specified name\n
/listusers <chatroom name>: lists the users currently in a chatroom\n
/send <chatroom name> <message>: send a message to a specific chatroom\n
/leavecr <name>: leave the chatroom with the specified name\n
/quit: closes the server\n"""

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
    user_list = []
    active = True
    

    print("Ready to accept connections")
    # Spinning up another thread to allow for it to accept connections and have the
    # server be able to run commands on it's own
    threading.Thread(target=accept_connections, args=(server_socket, server_chatrooms, user_list, active,), daemon=True).start()
    
    server_command = ""

    while active:
        server_command = input()
        given_command = server_command.split()

        match given_command[0]:
            case "/help":
                print(print_help())
            case "/history":
                if len(given_command) > 1:
                    output = ""
                    found = False
                    for i in server_chatrooms:
                        if i.name == given_command[1]:
                            found = True
                            output += "Room history for: " + i.name + "\n"
                            for j in i.history:
                                output += j[1] + ": " + j[2]
                    if not found:
                        output = "The specified room was not found"
                    print(output)
            case "/create":
                if len(given_command) > 1:
                    name = given_command[1]
                    add_new_room(server_chatrooms, lock, name)
            case "/listcr":
                chatlist = list_rooms(server_chatrooms)
                print("List of currently open chatrooms:\n")
                print(chatlist)
            case "/listusers":
                if len(given_command) > 1:
                    current_room = given_command[1]
                    users_in_room = list_connected_users(server_chatrooms, current_room)
                    print(users_in_room)
                else:
                    output = ""
                    for i in user_list:
                        if i == user_list[-1]:
                            output += i
                        else:
                            output += i + ", "
                    print(output)
            case "/quit":
                print("closing server...")
                lock.acquire()
                active = False
                lock.release()
            case other:
                print("Unknown command")

if __name__ == '__main__':
    main()
