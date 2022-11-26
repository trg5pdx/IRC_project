from socket import *
import time
import threading

def print_chatroom_list(rooms):
    room_list = rooms.split(";")

    output = "List of open chatrooms:\n"
    for i in room_list:
        if len(i) > 0:
            room = i.split(":")
            if room[1] == 1:
                output += room[0] + ": " + room[1] + " user connected\n"
            else:
                output += room[0] + ": " + room[1] + " users connected\n"
    return output 

def print_user_list(users, room):
    user_list = users.split(';')
    if len(user_list) == 0:
        return "No users are connected to " + room + "\n"
    
    output = "Users in " + room + ":\n"
    for i in user_list:
        if i == user_list[-1]:
            output += i
        else:
            output += i + ", "

    return output

def set_username(client_socket):
    while True:
        name = input("Enter your name:\n")
        connection_message = "trgIRC/0.1 CONNCT CLIENT\n"
        connection_message += "USERNAME " + name + "\n"
        
        try:
            client_socket.send(connection_message.encode())
            server_response = client_socket.recv(1024).decode()
            packet_lines = server_response.splitlines() 
            if packet_lines[0] == "trgIRC/0.1 CONNCT OK" and packet_lines[1] == "MESSAGE":
                    print(packet_lines[2])
                    return True
            elif packet_lines[0] == "trgIRC/0.1 CONNCT ERROR":
                match packet_lines[1]:
                    case "ERROR NAMEDUP":
                        print("Error, someone on the server is already using that name.")
                    case other:
                        print("Error, problem relating to formatting")
        except:
            print("Server has disconnected, closing client...")
            return False

def receive_server_responses(client_socket, active_connection, lock):
    while True:
        try:
            packet = client_socket.recv(1024).decode()
            if not packet:
                print("Server has disconnected, closing client...")
                lock.acquire()
                active_connection = False
                lock.release()
                break

            individual_packets = packet.split("trgIRC/0.1")
            for i in individual_packets:
                packet_lines = i.splitlines()
                
                msg_header = False
                help_ok = False
                listcr_ok = False
                listcr_err = False
                create_err = False
                joincr_ok = False 
                joincr_err = False
                listme_ok = False
                listme_err = False
                leavcr_ok = False
                leavcr_err = False
                msgchr_ok = False
                msgchr_err = False
                username = ""
                msg_time = 0
                room = ""
                message = "" 
                output = "" 
                
                # Not checking CONNCT as that's handled by the accept_connections function
                for i in packet_lines:
                    if not msg_header: 
                        line = i.split()
                        match line[0]:
                            case "HELP":
                                if line[1] == "OK":
                                    help_ok = True
                            case "LISTCR":
                                if line[1] == "OK":
                                    listcr_ok = True
                                else:
                                    print("No chatrooms are open")
                            case "CREATE":
                                if line[1] == "OK":
                                    print("Room created successfully")
                                else:
                                    create_err = True
                            case "JOINCR":
                                if line[1] == "OK":
                                    joincr_ok = True
                                else:
                                    joincr_err = True
                            case "LISTME":
                                if line[1] == "OK":
                                    listme_ok = True
                                else:
                                    listme_err = True
                            case "LEAVCR":
                                if line[1] == "OK":
                                    leavcr_ok = True
                                else:
                                    leavcr_err = True
                            case "MSGCHR":
                                if line[1] == "ERROR":
                                    msgchr_err = True
                                else:
                                    msgchr_ok = True
                            case "USERNAME":
                                username = line[1]
                            case "ROOM":
                                room = line[1]
                            case "TIME":
                                msg_time = line[1]
                            case "ERROR":
                                if create_err:
                                    if line[1] == "ROOMEXISTS":
                                        print("Failed, room already exists")
                                if joincr_err:
                                    if line[1] == "NOTFOUND":
                                        print("Failed to join, no room with that name")
                                if listme_err:
                                    if line[1] == "NOTFOUND":
                                        print("Failed to find that room")
                                if leavcr_err:
                                    if line[1] == "NOTFOUND":
                                        print("Couldn't find that room")
                                    if line[1] == "LEAVE":
                                        print("Failed to leave that room")
                                if msgchr_err:
                                    if line[1] == "NOTFOUND":
                                        print("Couldn't find that room")
                                    if line[1] == "NOTJOINED":
                                        print("Couldn't send message, not connected to chatroom")
                            case "MESSAGE":
                                msg_header = True
                            case "DSCTSV":
                                lock.acquire()
                                active_connection = False
                                lock.release()
                                print("Server has disconnected from the client, now shutting down...")
                                thread.exit()
                    else:
                        if help_ok:
                            i = i + '\n'
                            message += i
                        else:
                            message += i
                if help_ok:
                    output = message
                if joincr_ok:
                    output = "Succesfully joined " + room
                if listcr_ok:
                    output = print_chatroom_list(message)
                if listme_ok:
                    output = print_user_list(message, room)    
                if msgchr_ok:
                    output = "[" + room + "]" + username + ": " + message
                
                print(output)
        except:
            print("Server has disconnected, closing client...")
            lock.acquire()
            active_connection = False
            lock.release()
            thread.close()
