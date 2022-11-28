from socket import *
from enum import Enum
from Server import *
from Chat import *
import threading

Cmd = Enum('Cmd', ['Null', 'ListCR', 'Create', 'JoinCR', 'ListME', 
                   'LeavCR', 'Msgchr',])

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
                            message = "trgIRC/0.1 MSGCHR RECV\n"
                            message += "USERNAME " + rooms.history[i][1] + "\n"
                            message += "TIME " + str(rooms.history[i][0]) + "\n"
                            message += "ROOM " + rooms.name + "\n" 
                            message += "MESSAGE\n"
                            message += rooms.history[i][2]
                            self.client_socket.send(message.encode())
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
                    msg_header = False
                    packet_cmd = Cmd.Null 
                    selected_room = ""
                    user_message = ""
                    packet_lines = i.splitlines()
                    for j in packet_lines:
                        if not msg_header:
                            command = j.split()
                            match command[0]:
                                case "LISTCR":
                                    packet_cmd = Cmd.ListCR
                                case "CREATE":
                                    packet_cmd = Cmd.Create
                                case "JOINCR":
                                    packet_cmd = Cmd.JoinCR
                                case "LISTME":
                                    packet_cmd = Cmd.ListME
                                case "LEAVCR":
                                    packet_cmd = Cmd.LeavCR
                                case "MSGCHR":
                                    packet_cmd = Cmd.Msgchr
                                case "DSCTCL":
                                    self.__disconnecting(server_chatrooms, 
                                                         lock, user_list)
                                    return
                                case "MESSAGE":
                                    msg_header = True
                                case "REQUEST":
                                    # Doing this to check the formatting
                                    if packet_cmd == Cmd.Null:
                                        self.__send_misc_error()
                                        break
                                case "SEND":
                                    if packet_cmd != Cmd.Msgchr:
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
                            if packet_cmd == Cmd.Msgchr:
                                user_message += j
                            else:
                                self.__send_misc_error()
                                break
                    match packet_cmd:
                        case Cmd.ListCR:
                            self.__list_chatrooms(server_chatrooms)
                        case Cmd.Create:
                            self.__create_chatroom(server_chatrooms, 
                                                   selected_room) 
                        case Cmd.JoinCR:
                            self.__join_chatroom(server_chatrooms, 
                                                 selected_room, lock)
                        case Cmd.ListME:
                            self.__list_users_in_chatroom(server_chatrooms, 
                                                          selected_room)
                        case Cmd.LeavCR:
                            self.__leave_chatroom(selected_room, 
                                                  lock)
                        case Cmd.Msgchr:
                            self.__send_message_to_chatroom(
                                    server_chatrooms, lock, 
                                    selected_room, user_message) 
                        case Cmd.Null:
                            self.__send_misc_error()

    def __send_misc_error(self):
        error = "trgIRC/0.1 OTHER ERROR\n"
        error += "ERROR FORMAT\n"
        self.client_socket.send(error.encode())
    
    def __list_chatrooms(self, server_chatrooms):
        rooms = list_rooms(server_chatrooms)
        output = ""
        if len(rooms) > 0:
            output = "trgIRC/0.1 LISTCR OK\n"
            output += "MESSAGE\n"
            output += rooms
        else:
            output = "trgIRC/0.1 LISTCR ERROR\n"
            output += "ERROR EMPTY\n"
        self.client_socket.send(output.encode())

    def __create_chatroom(self, server_chatrooms, new_room_name):
        created = add_new_room(server_chatrooms, lock, new_room_name)
        output = ""
        if created:
            output = "trgIRC/0.1 CREATE OK\n"
            output += "ROOM " + new_room_name + "\n"
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
        output = ""
        for i in server_chatrooms:
            if room_name == i.name:
                found = True
                users = i.list_connected_users()
                if len(users) > 0:
                    output = "trgIRC/0.1 LISTME OK\n"
                    output += "ROOM " + i.name + "\n"
                    output += "MESSAGE\n"
                    output += users
                else:
                    output = "trgIRC/0.1 LISTME ERROR\n"
                    output += "ERROR EMPTY\n"
                    output += "ROOM " + room_name + "\n"
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


