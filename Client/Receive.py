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
        conn_error = False
        username = ""
        time = 0
        room = ""
        message = "" 
        
        for i in packet_lines:
            if not msg_header:
                line = i.split()
                
                match line[0]:
                    case "trgIRC/0.1":
                        if line[1] == "MSGCHR" and line[2] == "RECV":
                            msg_recv = True
                        if line[1] == "CONNCT" and line[2] == "OK":
                            connected = True
                        if line[1] == "CONNCT" and line[2] == "ERROR":
                            print("ERROR") 
                    case "USERNAME":
                        username = line[1]
                    case "ROOM":
                        room = line[1]
                    case "MESSAGE":
                        msg_header = True
            else:
                message += i
        

        if connected:
            output = message
        if msg_recv:
            output = "[" + room + "]" + username + ": " + message

        
        print(output)
