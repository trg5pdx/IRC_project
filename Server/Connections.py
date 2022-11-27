from socket import *
from Server import *
from Chat import *
import threading

class connections:
    def __init__(self, name, client_socket):
        self.name = name
        self.rooms = []
        self.client_socket = client_socket

    def send_messages(self, server_chatrooms, active):
        while active:
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

        if not active:
            closing_message = "trgIRC/0.1 DSCTSV\n"
            self.client_socket.send(closing_message.encode())
            thread.exit()

    def receive_message(self, server_chatrooms, lock, user_list, active):
        response = ""
        
        while active: 
            response = self.client_socket.recv(1024).decode()
            individual_packets = response.split("trgIRC/0.1")

            for i in individual_packets:
                if len(i) > 0:
                    # Flags for processing incoming packets, primarily for telling function
                    # how to interpret header lines and the message attached
                    msg_header = False
                    listcr_cmd = False
                    create_cmd = False
                    joincr_cmd = False
                    listme_cmd = False
                    leavcr_cmd = False
                    msgchr_cmd = False
                    selected_room = ""
                    user_message = ""
                    packet_lines = i.splitlines()
                    for j in packet_lines:
                        if not msg_header:
                            command = j.split()
                            match command[0]:
                                case "LISTCR":
                                    listcr_cmd = True
                                case "CREATE":
                                    create_cmd = True
                                case "JOINCR":
                                    joincr_cmd = True 
                                case "LISTME":
                                    listme_cmd = True
                                case "LEAVCR":
                                    leavcr_cmd = True
                                case "MSGCHR":
                                    msgchr_cmd = True
                                case "DSCTCL":
                                    self.__disconnecting(server_chatrooms, lock, user_list)
                                    return
                                case "MESSAGE":
                                    msg_header = True
                                case "REQUEST":
                                    # Doing this to check that the formattings correct
                                    if (not listcr_cmd or not leavcr_cmd or
                                        not create_cmd or not joincr_cmd or
                                        not listme_cmd):
                                        self.__send_misc_error()
                                        break
                                case "SEND":
                                    if not msgchr_cmd:
                                        self.__send_misc_error()
                                        break
                                case "ROOM":
                                    if len(command) > 1:
                                        selected_room = command[1]
                                    else:
                                        self.__send_misc_error()
                                        break
                                case other:
                                    self.__send_misc_error()
                                    break

                        else:
                            if msgchr_cmd:
                                user_message += j
                            else:
                                self.__send_misc_error()
                                break
                    if listcr_cmd:
                        self.__list_chatrooms(server_chatrooms)
                    if create_cmd:
                        self.__create_chatroom(server_chatrooms, selected_room) 
                    if joincr_cmd:
                        self.__join_chatroom(server_chatrooms, selected_room, lock)
                    if listme_cmd:
                        self.__list_users_in_chatroom(server_chatrooms, selected_room)
                    if leavcr_cmd:
                        self.__leave_chatroom(selected_room, lock)
                    if msgchr_cmd:
                        self.__send_message_to_chatroom(
                                server_chatrooms, lock, 
                                selected_room, user_message) 
    def __send_misc_error(self):
        error = "trgIRC/0.1 OTHER ERROR\n"
        error += "ERROR FORMAT\n"
        self.client_socket.send(error.encode())
    
    # Maybe come back and have it return an error for no chatrooms?
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
            output += "ROOM " + new_room_name + "\n"
        self.client_socket.send(output.encode())

    def __join_chatroom(self, server_chatrooms, room_name, lock):
        joined = False
        for i in server_chatrooms:
            if room_name == i.name:
                lock.acquire()
                i.join_chatroom(self.name)
                self.rooms.append([i.name, 0])
                joined = True
                lock.release()
                output = "trgIRC/0.1 JOINCR OK\n"
                output += "ROOM " + i.name + "\n"
                self.client_socket.send(output.encode())
        if not joined:
            output = "trgIRC/0.1 JOINCR ERROR\n"
            output += "ERROR NOTFOUND\n"
            output += "ROOM " + room_name + "\n"
            self.client_socket.send(output.encode())

    def __list_users_in_chatroom(self, server_chatrooms, room_name):
        found = False

        for i in server_chatrooms:
            if room_name == i.name:
                found = True
                users = i.list_connected_users()
                print("USERS: " + users + "\n")
                output = "trgIRC/0.1 LISTME OK\n"
                output += "ROOM " + i.name + "\n"
                output += "MESSAGE\n"
                output += users
                print("output: " + output + "\n")
                self.client_socket.send(output.encode())
        if not found:
            output = "trgIRC/0.1 LISTME ERROR\n"
            output += "ERROR NOTFOUND\n"
            output += "ROOM " + room_name + "\n"
            self.client_socket.send(output.encode())


    def __leave_chatroom(self, room_name, lock):
        found = False
        for i in server_chatrooms:
            if room_name == i.name:
                found = True
                lock.acquire()
                left = i.leave_chatroom(self.name)
                if left:
                    self.rooms.remove(room_name)
                    left_msg = self.name + " has disconnected from: " + i.name
                    i.history.append(left_msg)
                    output = "trgIRC/0.1 LEAVCR OK\n"
                    output += "ROOM " + room_name + "\n"
                    self.client_socket.send(output.encode())
                else:
                    output = "trgIRC/0.1 LEAVCR ERROR\n"
                    output += "ERROR LEAVE\n"
                    output += "ROOM " + room_name + "\n"
                    self.client_socket.send(output.encode())
                lock.release()
        if not found:
            output = "trgIRC/0.1 LEAVCR ERROR\n"
            output += "ERROR NOTFOUND\n"
            output += "ROOM " + room_name + "\n"
            self.client_socket.send(output.encode())

    def __send_message_to_chatroom(self, server_chatrooms, lock, room_name, user_message):
        found = False
        joined = False

        for i in server_chatrooms:
            if room_name == i.name:
                # checking if the user is connected to the specified room
                for user in i.userlist:
                    if self.name == user[1]:
                        joined = True
                        found = True
                        lock.acquire()
                        sent_message = [time.time(), self.name, user_message]
                        i.history.append(sent_message)
                        lock.release()
                if not joined:
                    found = True
                    output = "trgIRC/0.1 MSGCHR ERROR\n"
                    output += "ERROR NOTJOINED\n"
                    output += "ROOM " + room_name + "\n"
                    self.client_socket.send(output.encode())
        if not found:
            output = "trgIRC/0.1 MSGCHR ERROR\n"
            output += "ERROR NOTFOUND\n"
            output += "ROOM " + room_name + "\n"
            self.client_socket.send(output.encode())

    def __disconnecting(self, server_chatrooms, lock, user_list):    
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
        user_list.remove(self.name)
        lock.release()
        self.rooms = []
        print(self.name + " has disconnected from the server")
        self.client_socket.close()


