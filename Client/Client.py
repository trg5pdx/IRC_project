# Made by Thomas Gardner, 2022
# Using the TCP client example from the book to get set up

from socket import *
import sys
import threading
from Receive import *

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
    
    name = input("Enter your name:\n")
    connection_message = "trgIRC/0.1 CONNCT CLIENT\n"
    connection_message += "USERNAME " + name + "\n"

    client_socket.send(connection_message.encode())

    message = "" 
    default_room = ""
    quitting = False

    while not quitting:
        message = input()

        user_command = message.split(' ', 1)
        
        match user_command[0]:
            case "/help":
                request = "trgIRC/0.1 HELP\n"
                client_socket.send(request.encode())
            case "/listcr":
                request = "trgIRC/0.1 LISTCR\n"
                client_socket.send(request.encode())
            case "/create":
                if len(user_command) > 1:
                    request = "trgIRC/0.1 CREATE " + user_command[1] + "\n"
                    client_socket.send(request.encode())
                else:
                    print("incorrect number of arguments")
            case "/joincr":
                if len(user_command) > 1:
                    room_names = user_command[1].split()
                    for i in room_names:
                        request = "trgIRC/0.1 JOINCR " + i + "\n"
                        client_socket.send(request.encode())
                else:
                    print("Incorrect number of arguments")
            case "/leavecr":
                if len(user_command) > 1:
                    request = "trgIRC/0.1 LEAVCR " + user_command[1] + "\n"
                    client_socket.send(request.encode())
                else:
                    print("Incorrect number of arguments")
            case "/listusers": 
                if len(user_command) > 1:
                    request = "trgIRC/0.1 LISTME REQUEST " + user_command[1] + "\n"
                    client_socket.send(request.encode())
                else:
                    print("Incorrect number of arguments")
            case "/send":
                if len(user_command) > 1:
                    message_queue = user_command[1].split(';')
                    for i in message_queue:
                        room_message = i.split(' ', 1)
                        request = "trgIRC/0.1 MSGCHR REQUEST " + room_message[0] + "\n"
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
                quitting = True
            case other:
                if len(default_room) > 0:
                    client_command = "MSGCHR " + default_room + "\n" + message
                    client_socket.send(client_command.encode())
                else:
                    print("Entered invalid input")

    client_socket.close()
    sys.exit()

if __name__ == '__main__':
    main()
