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
        msg_header = False
        selected_room = ""
        user_message = ""
        
        while not disconnecting: 
            response = self.client_socket.recv(1024).decode()
            individual_packets = response.split("trgIRC/0.1")
             
            for i in individual_packets:
                if len(i) > 0:
                    packet_lines = i.splitlines()
                    for j in packet_lines:
                        if not msg_header:
                            client_command = j.split()
                            match client_command[0]:
                                case "HELP":
                                    help_message = "trgIRC/0.1 HELP OK\n"
                                    help_message += "MESSAGE\n"
                                    help_message += print_help()
                                    self.client_socket.send(help_message.encode())
                                case "LISTCR":
                                    # Look at having list_rooms throw an exception when 
                                    # there aren't any rooms
                                    self.__list_chatrooms(self, server_chatrooms)
                                case "CREATE":
                                    if len(client_command) > 1:
                                        self.__create_chatroom(server_chatrooms, client_command[1])
                                case "JOINCR":
                                    if len(client_command) > 1:
                                        # Come back and improve the error handling here
                                        self.__join_chatroom(server_chatrooms, client_command[1], lock)
                                case "LISTME":
                                    if len(client_command) > 2 and client_command[1] == "REQUEST":
                                        self.__list_users_in_chatroom(server_chatrooms, client_command[2])
                                case "LEAVCR":
                                    if len(client_command) > 1:
                                        self.__leave_chatroom(client_command[1], lock)
                                case "MSGCHR":
                                    if len(client_command) > 2:
                                        msgchr = True
                                        selected_room = client_command[2]
                                case "MSGCRS":
                                    print("placeholder!")
                                case "DSCTCL":
                                    self.__disconnecting(server_chatrooms, lock)
                                    disconnecting = True
                                case "MESSAGE":
                                    msg_header = True
                                case other:
                                    self.__send_misc_error()
                    else:
                        if msg_header and msgchr:
                            user_message += j
                
            if msg_header and msgchr:
                self.__send_message_to_chatroom(
                        server_chatrooms, lock, 
                        selected_room, user_message) 
                 

    def __send_misc_error(self):
        error = "trgIRC/0.1 OTHER ERROR\n"
        error += "ERROR FORMAT\n"
        self.client_socket.send(error.encode())

    def __list_chatrooms(self, server_chatrooms):
        rooms = list_rooms(server_chatrooms)
        output = "trgIRC/0.1 LISTCR OK\n"
        output += "MESSAGE\n"
        output += rooms
        self.client_socket.send(output.encode())

    def __create_chatroom(self, server_chatrooms, new_room_name):
        created = add_new_room(server_chatrooms, lock, new_room_name)
        output = ""
        if created:
            output = "trgIRC/0.1 CREATE OK\n"
        else:
            output = "trgIRC/0.1 CREATE ERROR\n"
            output += "ERROR ROOMEXISTS\n"
        self.client_socket.send(output.encode())

    def __join_chatroom(self, server_chatrooms, room_name, lock):
        joined = False
        for i in server_chatrooms:
            if room_name == i.name:
                lock.acquire()
                i.join_chatroom(self.name)
                self.rooms.append([i.name, time.time()])
                joined = True
                lock.release()
                output = "trgIRC/0.1 JOINCR OK\n"
                self.client_socket.send(output.encode())
        if not joined:
            output = "trgIRC/0.1 JOINCR ERROR\n"
            output += "ERROR NOTFOUND\n"
            self.client_socket.send(output.encode())

    def __list_users_in_chatroom(self, server_chatrooms, room_name):
        found = False

        for i in server_chatrooms:
            if room_name == i.name:
                found = True
                users = i.list_connected_users()
                print("USERS: " + users + "\n")
                output = "trgIRC/0.1 LISTME OK\n"
                # Maybe send back the room name for the client?
                output += "MESSAGE\n"
                output += users
                print("output: " + output + "\n")
                self.client_socket.send(output.encode())
        if not found:
            output = "trgIRC/0.1 LISTME ERROR\n"
            output += "ERROR NOTFOUND\n"
            self.client_socket.send(output.encode())


    def __leave_chatroom(self, room_name, lock):
        found = False
        for i in server_chatrooms:
            if room_name == i.name:
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

    def __send_message_to_chatroom(self, server_chatrooms, lock, room_name, user_message):
        found = False

        for i in server_chatrooms:
            if room_name == i.name:
                found = True
                lock.acquire()
                sent_message = [time.time(), self.name, user_message]
                i.history.append(sent_message)
                lock.release
        if not found:
            output = "trgIRC/0.1 MSGCHR ERROR\n"
            output += "ERROR NOTFOUND\n"
            self.client_socket.send(output.encode())
        

    def __disconnecting(self, server_chatrooms, lock):    
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
        print(self.name + " has disconnected from the server")
        self.client_socket.close()


