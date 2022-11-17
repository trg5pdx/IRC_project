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
                    client_socket.send("HELP".encode())
                case "/listcr":
                    client_socket.send("LISTCR YES".encode())
                case "/create":
                    if len(user_command) > 1:
                        client_command = "CREATE " + user_command[1]
                        client_socket.send(client_command.encode())
                case "/joincr":
                    if len(user_command) > 1:
                        client_command = "JOINCR " + user_command[1]
                        client_socket.send(client_command.encode())
                    else:
                        print("Incorrect number of arguments")
                case "/leavecr":
                    if len(user_command) > 1:
                        client_command = "LEAVCR " + user_command[1]
                        client_socket.send(client_command.encode())
                    else:
                        print("Incorrect number of arguments")
                case "/listusers":
                    if len(user_command) > 1:
                        client_command = "LISTME REQUEST " + user_command[1] + "\n"
                        client_socket.send(client_command.encode())
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

                case "/send":
                    if len(user_command) > 2:
                        client_command = "MSGCHR " + user_command[1] + "\n"
                        for i in range(2, len(user_command)):
                            word = user_command[i] + " "
                            client_command += word
                        client_socket.send(client_command.encode())
                    else:
                        print("Incorrect number of arguments")
                case "/default":
                    if len(user_command) > 1:
                        default_room = user_command[1]
                    # Getting the chatroom list and checking if the room the user provided is there
                    client_socket.send("LISTCR NO".encode())
                    server_resp = client_socket.recv(1024).decode()
                    room_list = server_resp.split(";") 
                    for i in room_list:
                        chatroom = i.split(":")
                        if chatroom[0] == user_command[1]:
                            default_room = chatroom[0]                         
                     
                case "/quit":
                    client_socket.send("DSCTCL".encode())
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
