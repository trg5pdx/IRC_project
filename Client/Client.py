# Made by Thomas Gardner, 2022
# Using the TCP client example from the book to get set up

from socket import *
from threading import Thread, Lock
import sys
from Receive import *

def print_help():
    return """
/help: prints this menu
/create <name>: creates a chatroom with the specified name
/listcr: lists the currently open chatrooms
/joincr <name>: join the chatroom with the specified name
/listusers <chatroom name>: lists the users currently in a chatroom
/default <chatroom name>: sets a default chatroom so anything you type without /send
    would be automatically sent to the set chatroom
/send <chatroom name> <message>: send a message to a specific chatroom
/leavecr <name>: leave the chatroom with the specified name
/quit: closes the server"""

def main():
    client_socket = socket(AF_INET, SOCK_STREAM)
    server_name = 'localhost'
    server_port = 45876 
        
    if len(sys.argv) > 1 and len(sys.argv) < 4:
        server_host = sys.argv[1]
        server_port = int(sys.argv[2])
        print("server host and port set at commandline")

    client_socket.connect((server_name, server_port))
    name_set = set_username(client_socket)
    quitting = False 
    message = "" 
    default_room = ""
    lock = Lock()
    
    if not name_set:
        client_socket.close()
        sys.exit()
    
    server_responses = Thread(target=receive_server_responses, args=(client_socket, lock,), daemon=True)
    server_responses.start()

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
                client_socket.send(request.encode())
            case "/create":
                if len(user_command) > 1:
                    request = "trgIRC/0.1 CREATE REQUEST\n" 
                    request += "ROOM " + user_command[1] + "\n"
                    client_socket.send(request.encode())
                else:
                    print("Incorrect number of arguments")
            case "/joincr":
                if len(user_command) > 1:
                    room_names = user_command[1].split()
                    for i in room_names:
                        request = "trgIRC/0.1 JOINCR REQUEST\n" 
                        request += "ROOM " + i + "\n"
                        client_socket.send(request.encode())
                else:
                    print("Incorrect number of arguments")
            case "/leavecr":
                if len(user_command) > 1:
                    request = "trgIRC/0.1 LEAVCR REQUEST\n" 
                    request += "ROOM " + user_command[1] + "\n"
                    client_socket.send(request.encode())
                else:
                    print("Incorrect number of arguments")
            case "/listusers": 
                if len(user_command) > 1:
                    request = "trgIRC/0.1 LISTME REQUEST\n" 
                    request += "ROOM " + user_command[1] + "\n"
                    client_socket.send(request.encode())
                else:
                    print("Incorrect number of arguments")
            case "/send":
                if len(user_command) > 1:
                    message_queue = user_command[1].split(';')
                    for i in message_queue:
                        room_message = i.split(' ', 1)
                        request = "trgIRC/0.1 MSGCHR SEND\n" 
                        request += "ROOM " + room_message[0] + "\n"
                        request += "MESSAGE\n"
                        request += room_message[1]
                        client_socket.send(request.encode())
                else:
                    print("Incorrect number of arguments")
            case "/default":
                if len(user_command) > 1:
                    default_room = user_command[1]
                # Getting the chatroom list and checking if the room the user provided is there
                client_socket.send("trgIRC/0.1 LISTCR\n".encode())
                server_resp = client_socket.recv(1024).decode()
                room_list = server_resp.split(";") 
                found = False
                for i in room_list:
                    chatroom = i.split(":")
                    if chatroom[0] == user_command[1]:
                        found = True
                        default_room = chatroom[0]                         
                        print("Default chatroom has been set")
                if not found:
                    print("Failed to set default room: Couldn't find the specified chatroom")

            case "/quit":
                client_socket.send("trgIRC/0.1 DSCTCL\n".encode())
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

                    client_socket.send(client_command.encode())
                else:
                    print("Entered invalid input")
    client_socket.close()
    sys.exit()

if __name__ == '__main__':
    main()
