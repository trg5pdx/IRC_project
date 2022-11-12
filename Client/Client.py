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
    
    name = input("Enter your name:\n")
    connection_message = "CONNCT " + name 

    client_socket.send(connection_message.encode())

    message = "" 
    
    quitting = False

    while not quitting:
        message = input()

        if message[0] == "/":
            user_command = message.split()
            
            match user_command[0]:
                case "/help":
                    client_socket.send("HELP".encode())
                case "/listcr":
                    client_socket.send("LISTCR".encode())
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
                case "/quit":
                    client_socket.send("DSCTSV".encode())
                    print("Disconnecting...")
                    quitting = True

        else:
            client_socket.send(message.encode())


    client_socket.close()
    sys.exit()

if __name__ == '__main__':
    main()
