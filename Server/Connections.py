# Made by Thomas Gardner, 2022

from socket import *
from enum import Enum
from threading import Thread, Lock
from Server import *
from Chat import *

Cmd = Enum('Cmd', ['Null', 'ListCR', 'Create', 'JoinCR', 'ListME', 
                   'LeavCR', 'Msgchr', 'Alive'])

class connections:
    def __init__(self, name, client_socket, address, port):
        self.name = name
        self.rooms = []
        self.client_socket = client_socket
        self.address = address
        self.port = port
        self.is_active = True

    def send_messages(self, server_chatrooms, lock, user_list, server_active):
        try:
            while server_active and self.is_active:
                for rooms in server_chatrooms:
                    for user_room in self.rooms:
                        if (user_room[0] == rooms.name 
                            and len(rooms.history) > user_room[1]):
                            i = user_room[1]
                            while i < len(rooms.history):
                                message = ("trgIRC/0.1 MSGCHR RECV\n" +
                                    "USERNAME " + rooms.history[i][1] + "\n" +
                                    "TIME " + str(rooms.history[i][0]) + "\n" +
                                    "ROOM " + rooms.name + "\n" +
                                    "MESSAGE\n" +
                                    rooms.history[i][2])
                                self.client_socket.sendall(message.encode())
                                i += 1
                            user_room[1] = i
            if not server_active:
                closing_message = "trgIRC/0.1 DSCTSV\n"
                self.client_socket.sendall(closing_message.encode())
                return
            if not self.is_active:
                return
        except Exception as e:
            print("Exception: ({}) failed to send message to client".format(e))
            self.__disconnecting(server_chatrooms, lock, user_list)

    def receive_message(self, server_chatrooms, lock, user_list, server_active):
        response = ""
        
        while server_active and self.is_active: 
            try:
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
                                    case "ALIVE":
                                        packet_cmd = Cmd.Alive
                                    case "DSCTCL":
                                        self.__disconnecting(server_chatrooms, 
                                                             lock, user_list)
                                        return
                                    case "MESSAGE":
                                        msg_header = True
                                    case "REQUEST":
                                        # Doing this to check the formatting
                                        if packet_cmd == Cmd.Null:
                                            self.__send_misc_error(lock, user_list)
                                            break
                                    case "SEND":
                                        if packet_cmd != Cmd.Msgchr:
                                            self.__send_misc_error(lock, user_list)
                                            break
                                    case "ROOM":
                                        if len(command) > 1:
                                            selected_room = command[1]
                                        else:
                                            self.__send_misc_error(lock, user_list)
                                            break
                                    case other:
                                        self.__send_misc_error(lock, user_list)
                                        break
                            else:
                                if packet_cmd == Cmd.Msgchr:
                                    user_message += j
                                else:
                                    self.__send_misc_error(lock, user_list)
                                    break
                        match packet_cmd:
                            case Cmd.ListCR:
                                self.__list_chatrooms(server_chatrooms, lock, user_list)
                            case Cmd.Create:
                                self.__create_chatroom(server_chatrooms, user_list, 
                                                       lock, selected_room) 
                            case Cmd.JoinCR:
                                self.__join_chatroom(server_chatrooms, user_list,
                                                     selected_room, lock)
                            case Cmd.ListME:
                                self.__list_users_in_chatroom(server_chatrooms, user_list,
                                                              selected_room, lock)
                            case Cmd.LeavCR:
                                self.__leave_chatroom(server_chatrooms, user_list,
                                                      selected_room, lock)
                            case Cmd.Msgchr:
                                self.__send_message_to_chatroom(
                                        server_chatrooms, user_list, lock, 
                                        selected_room, user_message) 
                            case Cmd.Alive:
                                alive_ping = "trgIRC/0.1 ALIVE OK\n"
                                self.client_socket.send(alive_ping.encode())
                            case Cmd.Null:
                                self.__send_misc_error(lock, user_list)
            except Exception as e:
                print("Exception: ({}) failed to receive message from client".format(e))
                self.__disconnecting(server_chatrooms, lock, user_list)
        if not self.is_active:
            return

    def __send_misc_error(self, lock, user_list):
        try:
            error = ("trgIRC/0.1 OTHER ERROR\n" +
                    "ERROR FORMAT\n")
            self.client_socket.sendall(error.encode())
        except Exception as e:
            print("Exception: %; Failed to send message to client"%(e))
            print("Client: %s (%s:%s)"%(self.name, self.address, self.port))
            self.__disconnecting(server_chatrooms, lock, user_list)
    
    def __list_chatrooms(self, server_chatrooms, lock, user_list):
        try:
            rooms = list_rooms(server_chatrooms)
            output = ""
            if len(rooms) > 0:
                output = ("trgIRC/0.1 LISTCR OK\n" + 
                        "MESSAGE\n" + 
                        rooms)
            else:
                output = ("trgIRC/0.1 LISTCR ERROR\n" +
                        "ERROR EMPTY\n")
            self.client_socket.send(output.encode())
        except Exception as e:
            print("Exception: ({}); Failed to send message to client".format(e))
            print("Client: {} ({}:{})".format(self.name, self.address, self.port))
            self.__disconnecting(server_chatrooms, lock, user_list)

    def __create_chatroom(self, server_chatrooms, user_list, lock, new_room_name):
        try:
            created = add_new_room(server_chatrooms, lock, new_room_name)
            output = ""
            if created:
                output = ("trgIRC/0.1 CREATE OK\n" +
                        "ROOM " + new_room_name + "\n")
            else:
                output = ("trgIRC/0.1 CREATE ERROR\n" +
                        "ERROR ROOMEXISTS\n" +
                        "ROOM " + new_room_name + "\n")
            self.client_socket.sendall(output.encode())
        except Exception as e:
            print("Exception: ({}); Failed to send message to client".format(e))
            print("Client: {} ({}:{})".format(self.name, self.address, self.port))
            self.__disconnecting(server_chatrooms, lock, user_list)

    def __join_chatroom(self, server_chatrooms, user_list, room_name, lock):
        joined = False
        try:
            for i in server_chatrooms:
                if room_name == i.name:
                    lock.acquire()
                    i.join_chatroom(self.name)
                    join_msg = self.name + " has joined " + i.name
                    i.history.append([time.time(), "ServerMessage", join_msg])
                    self.rooms.append([i.name, 0])
                    joined = True
                    lock.release()
                    output = ("trgIRC/0.1 JOINCR OK\n" +
                            "ROOM " + i.name + "\n")
                    self.client_socket.send(output.encode())
            if not joined:
                output = ("trgIRC/0.1 JOINCR ERROR\n" +
                        "ERROR NOTFOUND\n" +
                        "ROOM " + room_name + "\n")
                self.client_socket.sendall(output.encode())
        except Exception as e:
            print("Exception: ({}); Failed to send message to client".format(e))
            print("Client: {} ({}:{})".format(self.name, self.address, self.port))
            self.__disconnecting(server_chatrooms, lock, user_list)

    def __list_users_in_chatroom(self, server_chatrooms, user_list, room_name, lock):
        found = False
        output = ""
        try:
            for i in server_chatrooms:
                if room_name == i.name:
                    found = True
                    users = i.list_connected_users()
                    if len(users) > 0:
                        output = ("trgIRC/0.1 LISTME OK\n" +
                                "ROOM " + i.name + "\n" +
                                "MESSAGE\n" +
                                users)
                    else:
                        output = ("trgIRC/0.1 LISTME ERROR\n" +
                                "ERROR EMPTY\n" +
                                "ROOM " + room_name + "\n")
            if not found:
                output = "trgIRC/0.1 LISTME ERROR\n"
                output += "ERROR NOTFOUND\n"
                output += "ROOM " + room_name + "\n"
            self.client_socket.sendall(output.encode())
        except Exception as e:
            print("Exception: ({}); Failed to send message to client".format(e))
            print("Client: {} ({}:{})".format(self.name, self.address, self.port))
            self.__disconnecting(server_chatrooms, lock, user_list)

    def __leave_chatroom(self, server_chatrooms, user_list, room_name, lock):
        found = False
        try:
            for i in server_chatrooms:
                if room_name == i.name:
                    found = True
                    lock.acquire()
                    left = i.leave_chatroom(self.name)
                    if left:
                        for j in range(len(self.rooms)):
                            if self.rooms[j][0] == i.name:
                                self.rooms.pop(j)
                        left_msg = self.name + " has disconnected from " + i.name
                        i.history.append([time.time(), "ServerMessage", left_msg])
                        output = ("trgIRC/0.1 LEAVCR OK\n" +
                                "ROOM " + room_name + "\n")
                        self.client_socket.sendall(output.encode())
                    else:
                        output = ("trgIRC/0.1 LEAVCR ERROR\n" +
                                "ERROR LEAVE\n" +
                                "ROOM " + room_name + "\n")
                        self.client_socket.sendall(output.encode())
                    lock.release()
            if not found:
                output = ("trgIRC/0.1 LEAVCR ERROR\n" +
                        "ERROR NOTFOUND\n" +
                        "ROOM " + room_name + "\n")
                self.client_socket.sendall(output.encode())
        except Exception as e:
            print("Exception: ({}); Failed to send message to client".format(e))
            print("Client: {} ({}:{})".format(self.name, self.address, self.port))
            self.__disconnecting(server_chatrooms, lock, user_list)

    def __send_message_to_chatroom(self, server_chatrooms, user_list, lock, 
                                   room_name, user_message):
        found = False
        joined = False
        try:
            for i in server_chatrooms:
                if room_name == i.name:
                    # checking if the user is connected to the specified room
                    for user in i.userlist:
                        if self.name == user[1]:
                            joined = True
                            found = True
                            lock.acquire()
                            sent_message = [time.time(), 
                                            self.name, 
                                            user_message]
                            i.history.append(sent_message)
                            lock.release()
                    if not joined:
                        found = True
                        output = ("trgIRC/0.1 MSGCHR ERROR\n" +
                                "ERROR NOTJOINED\n" +
                                "ROOM " + room_name + "\n")
                        self.client_socket.send(output.encode())
            if not found:
                output = ("trgIRC/0.1 MSGCHR ERROR\n" +
                        "ERROR NOTFOUND\n" +
                        "ROOM " + room_name + "\n")
                self.client_socket.send(output.encode())
        except Exception as e:
            print("Exception: ({}); Failed to send message to client".format(e))
            print("Client: {} ({}:{})".format(self.name, self.address, self.port))
            self.__disconnecting(server_chatrooms, lock, user_list)

    def __disconnecting(self, server_chatrooms, lock, user_list):    
        if self.is_active:
            lock.acquire()
            for i in self.rooms:
                for j in server_chatrooms:
                    if j.name == i[0]:
                        left = j.leave_chatroom(self.name)
                        if not left:
                            # COME BACK TO
                            print("failed to leave chatroom")
                            print(j.userlist)
                        else:
                            left_msg = self.name + " has disconnected from " + j.name
                            j.history.append([time.time(), "ServerMessage", left_msg])
            user_list.remove(self.name)
            lock.release()
            self.rooms = []
            print("User " + self.name + " (" + self.address + ":" + self.port + 
                  ") " + "has disconnected")
            self.is_active = False
            self.client_socket.close()
