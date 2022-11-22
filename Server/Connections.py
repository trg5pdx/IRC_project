from socket import *
from Server import *
from Chat import *
import threading

class connections:
    def __init__(self, name, client_socket):
        self.name = name
        self.rooms = []
        self.client_socket = client_socket

    def send_messages(self, server_chatrooms):
        while True:
            for rooms in server_chatrooms:
                for user_room in self.rooms:
                    if user_room[0] == rooms.name and len(rooms.history) > user_room[1]:
                        i = user_room[1]
                        while i < len(rooms.history):
                            user_message = "trgIRC/0.1 MSGCHR RECV\n"
                            user_message += "USERNAME " + rooms.history[i][1] + "\n"
                            user_message += "TIME " + str(rooms.history[i][0]) + "\n"
                            user_message += "ROOM " + rooms.name + "\n" 
                            user_message += "MESSAGE\n"
                            user_message += rooms.history[i][2]
                            self.client_socket.send(user_message.encode())
                            i += 1
                        user_room[1] = i

    def receive_message(self, server_chatrooms, lock):
        response = ""
        disconnecting = False

        # Flags for processing incoming packets, primarily for telling function
        # how to interpret header lines and the message attached
        msgchr = False
        msgchrs = False

        with self.client_socket:
            while not disconnecting: 
                response = self.client_socket.recv(1024).decode()
                packet_lines = response.splitlines()
                client_command = packet_lines[0].split()
                
                """
                if client_command[0] == "trgIRC/0.1":
                    continue
                else:
                    # Come back to the error on this was, just used other since I didn't have anything else in mind
                    # for telling the client the packet format was incorrect
                    error_message = "trgIRC/0.1 OTHER ERROR\n"
                    error_message += "ERROR FORMAT\n"
                    self.client_socket.send(error_message.encode())
                """
                match client_command[1]:
                    case "HELP":
                        help_message = "trgIRC/0.1 HELP OK\n"
                        help_message += "MESSAGE\n"
                        help_message += print_help()
                        self.client_socket.send(help_message.encode())
                    case "LISTCR":
                        # Look at having list_rooms throw an exception when there aren't any rooms
                        rooms = list_rooms(server_chatrooms)
                        output = "trgIRC/0.1 LISTCR OK\n"
                        output += "MESSAGE\n"
                        output += rooms
                        self.client_socket.send(output.encode())
                    case "CREATE":
                        if len(client_command) > 2:
                            new_room_name = client_command[2]
                            created = add_new_room(server_chatrooms, lock, new_room_name)
                            output = ""
                            if created:
                                output = "trgIRC/0.1 CREATE OK\n"
                            else:
                                output = "trgIRC/0.1 CREATE ERROR\n"
                                output += "ERROR ROOMEXISTS\n"
                            self.client_socket.send(output.encode())
                    case "JOINCR":
                        joined = False
                        if len(client_command) > 2:
                            # Come back and improve the error handling here
                            for i in server_chatrooms:
                                if i.name == client_command[2]:
                                    i.join_chatroom(self.name)
                                    self.rooms.append([i.name, 0])
                                    joined = True

                        if joined:
                            output = "trgIRC/0.1 JOINCR OK\n"
                            self.client_socket.send(output.encode())
                        else:
                            output = "trgIRC/0.1 JOINCR ERROR\n"
                            output += "ERROR NOTFOUND\n"
                            self.client_socket.send(output.encode())

                    case "LISTME":
                        found = False
                        if len(client_command) > 3 and client_command[2] == "REQUEST":
                            for i in server_chatrooms:
                                if client_command[3] == i.name:
                                    found = True
                                    users = i.list_connected_users()
                                    output = "trgIRC LISTME OK\n"
                                    output += "MESSAGE\n"
                                    output += users
                                    self.client_socket.send(output.encode())
                        if not found:
                            output = "trgIRC/0.1 LISTME ERROR\n"
                            output += "ERROR NOTFOUND\n"
                            self.client_socket.send(output.encode())
                    case "LEAVCR":
                        found = False
                        if len(client_command) > 2:
                            for i in server_chatrooms:
                                if client_command[2] == i.name:
                                    found = True
                                    lock.acquire()
                                    left = i.leave_chatroom(self.name)
                                    if left:
                                        self.rooms.remove(client_command[2])
                                        left_msg = self.name + " has disconnected from: " + i.name
                                        i.history.append(left_msg)
                                        output = "trgIRC/0.1 LEAVCR OK\n"
                                        self.client_socket.send(output.encode())
                                    else:
                                        output = "trgIRC/0.1 LEAVCR ERROR\n"
                                        output += "ERROR LEAVE\n"
                                        self.client_socket.send(output.encode())
                                    lock.release()
                        if not found:
                            output = "trgIRC/0.1 LEAVCR ERROR\n"
                            output += "ERROR NOTFOUND\n"
                            self.client_socket.send(output.encode())
                    case "MSGCHR":
                        found = False
                        if len(client_command) > 3:
                            for i in server_chatrooms:
                                if client_command[2] == "REQUEST" and client_command[3] == i.name:
                                    found = True
                                    lock.acquire()
                                    user_message = "";
                                    for j in range(2, len(packet_lines)):
                                        user_message += packet_lines[j]
                                    sent_message = [time.time(), self.name, user_message]
                                    i.history.append(sent_message) 
                                    lock.release()
                        if not found:
                            output = "trgIRC/0.1 MSGCHR ERROR\n"
                            output += "ERROR NOTFOUND\n"
                            self.client_socket.send(output.encode())
                    case "MSGCRS":
                        print("placeholder!")
                    case "DSCTCL":
                        lock.acquire()
                        for i in self.rooms:
                            for j in server_chatrooms:
                                if j.name == i:
                                    left = j.leave_chatroom(self.name)
                                    if not left:
                                        # COME BACK TO
                                        print("failed to leave chatroom")
                                        print(j.userlist)
                                    else:
                                        left_msg = self.name + " has disconnected from: " + j.name
                                        j.history.append(left_msg)
                        lock.release()
                        self.rooms = []
                        disconnecting = True
                        self.client_socket.close()
                    case other:
                        self.client_socket.send("Server doesn't recognize client command\n".encode())
