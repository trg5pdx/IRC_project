# Made by Thomas Gardner, 2022
# Using the TCP client example from the book to get set up

from socket import *
from threading import Thread, Lock
import sys
import time
from Receive import *

def print_help():
    return """
/help: prints this menu
/create <name>: creates a chatroom with the specified name
/listcr: lists the currently open chatrooms
/joincr <name>: join the chatroom with the specified name
/listusers <chatroom name>: lists the users currently in a chatroom
/default <chatroom name>: sets a default chatroom so anything you type without 
        /send would be automatically sent to the set chatroom
/send <chatroom name> <message>: send a message to a specific chatroom
/leavecr <name>: leave the chatroom with the specified name
/quit: closes the server"""

def keep_connection_alive(client_socket, lock):
    try:
        while True:
            time.sleep(20)
            # Acquiring a lock to avoid having it send while 
            # the clients attempting to send elsewhere
            lock.acquire()
            alive_msg = "trgIRC/0.1 ALIVE REQUEST\n"
            client_socket.sendall(alive_msg.encode())
            lock.release()
    except Exception as e:
        print("Exception: ({}) has occured, closing the client")
        return

def main():
    client_socket = socket(AF_INET, SOCK_STREAM)
    server_name = 'localhost'
    server_port = 45870
        
    if len(sys.argv) > 1 and len(sys.argv) < 4:
        server_host = sys.argv[1]
        server_port = int(sys.argv[2])
        print("server host and port set at commandline")

    client_socket.connect((server_name, server_port))
    client_socket.settimeout(40)
    name_set = set_username(client_socket)
    quitting = False 
    message = "" 
    default_room = ""
    lock = Lock()
    
    if not name_set:
        client_socket.close()
        sys.exit()
    
    server_responses = Thread(target=receive_server_responses, 
                              args=(client_socket, lock,), daemon=True)
    keep_alive = Thread(target=keep_connection_alive,
                          args=(client_socket, lock,), daemon=True)

    server_responses.start()
    keep_alive.start()

    while not quitting:
        message = input()
        if not server_responses.is_alive():
            sys.exit()

        user_command = message.split(' ', 1)
        
        match user_command[0]:
            case "/help":
                print(print_help())
            case "/listcr":
                request = "trgIRC/0.1 LISTCR REQUEST\n"
                client_socket.sendall(request.encode())
            case "/create":
                if len(user_command) > 1:
                    request = "trgIRC/0.1 CREATE REQUEST\n" 
                    request += "ROOM " + user_command[1] + "\n"
                    client_socket.sendall(request.encode())
                else:
                    print("Incorrect number of arguments")
            case "/joincr":
                if len(user_command) > 1:
                    room_names = user_command[1].split()
                    for i in room_names:
                        request = "trgIRC/0.1 JOINCR REQUEST\n" 
                        request += "ROOM " + i + "\n"
                        client_socket.sendall(request.encode())
                else:
                    print("Incorrect number of arguments")
            case "/leavecr":
                if len(user_command) > 1:
                    request = "trgIRC/0.1 LEAVCR REQUEST\n" 
                    request += "ROOM " + user_command[1] + "\n"
                    client_socket.sendall(request.encode())
                else:
                    print("Incorrect number of arguments")
            case "/listusers": 
                if len(user_command) > 1:
                    request = "trgIRC/0.1 LISTME REQUEST\n" 
                    request += "ROOM " + user_command[1] + "\n"
                    client_socket.sendall(request.encode())
                else:
                    print("Incorrect number of arguments")
            case "/send":
                if len(user_command) > 1:
                    message_queue = user_command[1].split(';')
                    for i in message_queue:
                        room_message = i.split(' ', 1)
                        request = "trgIRC/0.1 MSGCHR SEND\n" 
                        request += "ROOM " + room_message[0].strip() + "\n"
                        request += "MESSAGE\n"
                        request += room_message[1]
                        client_socket.sendall(request.encode())
                else:
                    print("Incorrect number of arguments")
            case "/default":
                if len(user_command) > 1:
                    # Getting the chatroom list and checking if the room the 
                    # user provided is there
                    client_socket.sendall("trgIRC/0.1 LISTCR REQUEST\n".encode())
                    server_resp = client_socket.recv(1024).decode()
                    server_message = server_resp.split("MESSAGE") 
                    room_list = server_message[1].split(";")
                    print(room_list)
                    found = False
                    for i in room_list:
                        chatroom = i.strip().split(":")
                        if chatroom[0] == user_command[1]:
                            found = True
                            default_room = user_command[1]
                            print("Default chatroom has been set")
                    if not found:
                        print("Failed to set default room: room doesn't exist")
                else:
                    print("Incorrect number of arguments")
            case "/quit":
                client_socket.sendall("trgIRC/0.1 DSCTCL\n".encode())
                print("Disconnecting...")
                lock.acquire()
                quitting = True 
                lock.release()
            case other:
                if len(default_room) > 0:
                    client_command = "trgIRC/0.1 MSGCHR SEND\n"
                    client_command += "ROOM " + default_room + "\n"
                    client_command += "MESSAGE\n"
                    client_command += message

                    client_socket.sendall(client_command.encode())
                else:
                    print("Entered invalid input")
    client_socket.close()
    sys.exit()

if __name__ == '__main__':
    main()
