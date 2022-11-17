from socket import *
import time

def receive_server_responses(client_socket):
    while True:
        packet = client_socket.recv(1024).decode()
        packet_lines = packet.splitlines()
        output = "" 
        
        """
        Thoughts on how to process packets:
        have flags set up at the beginning of the function that would get flipped as it parses
        each line, with it exiting the loop once it hits the message line, indicating
        the beginning of the message being sent over. Using the information provided in the headers,
        the client will then format the chat message how it wants and print it out to the user
        """
        msg_recv = False
        msg_header = False
        connected = False
        conn_err = False
        listcr_ok = False
        listcr_fancy = True # Expecting true as thats the option that requires no action
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
        time = 0
        room = ""
        message = "" 
        
        for i in packet_lines:
            if not msg_header: 
                line = i.split()
                
                match line[0]:
                    case "trgIRC/0.1":
                        match line[1]:
                            case "MSGCHR":
                                if line[2] == "RECV":
                                    msg_recv = True
                            case "CONNCT":
                                if line[2] == "OK":
                                    connected = True
                                else:
                                    conn_err = True
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
                                if line[2] == "OK":
                                    msgchr_ok = True
                                else:
                                    msgchr_err = True
                    case "USERNAME":
                        username = line[1]
                    case "ROOM":
                        room = line[1]
                    case "FANCY":
                        # Only checking for false as otherwise it will be printed like any other msg
                        if line[1] == "FALSE":
                            print("placeholder! add a function for format this neatly later")
                            listcr_fancy = False
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
                message += i
        
        if connected or listcr_fancy:
            output = message
        if msg_recv:
            if msgchr_ok:
                output = "[" + room + "]" + username + ": " + message

        
        print(output)
