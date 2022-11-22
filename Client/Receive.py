from socket import *
import time

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

def receive_server_responses(client_socket):
    while True:
        packet = client_socket.recv(1024).decode()
        packet_lines = packet.splitlines()
        
        msg_header = False
        connected = False
        conn_err = False
        help_ok = False
        listcr_ok = False
        listcr_err = False
        create_err = False
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
        
        for i in packet_lines:
            if not msg_header: 
                line = i.split()
                
                match line[0]:
                    case "trgIRC/0.1":
                        match line[1]:
                            case "CONNCT":
                                if line[2] == "OK":
                                    connected = True
                                else:
                                    conn_err = True
                            case "HELP":
                                if line[2] == "OK":
                                    help_ok = True
                            case "LISTCR":
                                if line[2] == "OK":
                                    listcr_ok = True
                                else:
                                    print("No chatrooms are open")
                            case "CREATE":
                                if line[2] == "OK":
                                    print("Room created successfully")
                                else:
                                    create_err = True
                            case "JOINCR":
                                if line[2] == "OK":
                                    print("Successfully joined room\n")
                                else:
                                    joincr_err = True
                            case "LISTME":
                                if line[2] == "OK":
                                    listme_ok = True
                                else:
                                    listme_err = True
                            case "LEAVCR":
                                if line[2] == "OK":
                                    leavcr_ok = True
                                else:
                                    leavcr_err = True
                            case "MSGCHR":
                                if line[2] == "ERROR":
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
                        if conn_err:
                            # Come back later to have the user reenter a username
                            print("Error failed to connect")
                        if create_err:
                            if line[1] == "ROOMEXISTS":
                                print("Failed, room already exists")
                        if joincr_err:
                            if line[1] == "NOTFOUND":
                                print("Failed to join, couldn't find room with that name")
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
                    case "MESSAGE":
                        msg_header = True
            else:
                if help_ok:
                    i = i + '\n'
                    message += i
                else:
                    message += i
        if connected or help_ok:
            output = message
        if listcr_ok:
            output = print_chatroom_list(message)
        if msgchr_ok:
            output = "[" + room + "]" + username + ": " + message
            print("output: " + output)
        
        print(output)
