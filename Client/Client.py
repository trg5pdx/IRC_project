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

        if message[0] == "/":
            user_command = message.split()
            
            match user_command[0]:
                case "/help":
                    request = "trgIRC/0.1 HELP\n"
                    client_socket.send(request.encode())
                case "/listcr":
                    request = "trgIRC/0.1 LISTCR YES\n"
                    client_socket.send(request.encode())
                case "/create":
                    if len(user_command) > 1:
                        request = "trgIRC/0.1 CREATE " + user_command[1] + "\n"
                        client_socket.send(request.encode())
                    else:
                        print("incorrect number of arguments")
                case "/joincr":
                    if len(user_command) > 1:
                        request = "trgIRC/0.1 JOINCR " + user_command[1] + "\n"
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
                        server_resp = client_socket.recv(1024).decode()
                        user_list = server_resp.split(";")
                        formatted_user_list = ""

                        for i in user_list:
                            if i == user_list[-1]:
                                formatted_user_list += i
                            else:
                                current = i + ", "
                                formatted_user_list += current
                        print("Users currently connected to " + user_command[1])
                        print(formatted_user_list)
                    else:
                        print("Incorrect number of arguments")
                case "/send":
                    if len(user_command) > 2:
                        request = "trgIRC/0.1 MSGCHR REQUEST " + user_command[1] + "\n"
                        request += "MESSAGE\n"
                        for i in range(2, len(user_command)):
                            word = user_command[i] + " "
                            request += word
                        client_socket.send(request.encode())
                    else:
                        print("Incorrect number of arguments")
                case "/default":
                    if len(user_command) > 1:
                        default_room = user_command[1]
                    # Getting the chatroom list and checking if the room the user provided is there
                    client_socket.send("trgIRC/0.1 LISTCR NO\n".encode())
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
        # Redo this to make it more clear; currently checks if the default rooms been set
        elif default_room:
            client_command = "MSGCHR " + default_room + "\n" + message
            client_socket.send(client_command.encode())
        else:
            print("Entered invalid input")


    client_socket.close()
    sys.exit()

if __name__ == '__main__':
    main()
