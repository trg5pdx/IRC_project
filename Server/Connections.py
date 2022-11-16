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
                            user_message = "[" + rooms.name + "]" + rooms.history[i]
                            self.client_socket.send(user_message.encode())
                            i += 1
                        user_room[1] = i

    def receive_message(self, server_chatrooms, lock):
        response = ""

        with self.client_socket:
            while response != "DSCTCL":
                response = self.client_socket.recv(1024).decode()
                packet_lines = response.splitlines()
                client_command = packet_lines[0].split()

                match client_command[0]:
                    case "HELP":
                        help_message = print_help()
                        self.client_socket.send(help_message.encode())
                    case "LISTCR":
                        if len(client_command) > 1: 
                            fancy_option = client_command[1]
                            fancy = True
                            
                            if fancy_option == "YES":
                                fancy = True
                            else:
                                fancy = False

                            rooms = list_rooms(server_chatrooms, fancy)
                            self.client_socket.send(rooms.encode())
                        else:
                            rooms = list_rooms(server_chatrooms, True)
                            self.client_socket.send(rooms.encode())
                    case "CREATE":
                        if len(client_command) > 1:
                            new_room_name = client_command[1]
                            add_new_room(server_chatrooms, lock, new_room_name)
                    case "JOINCR":
                        if len(client_command) > 1:
                            # Come back and improve the error handling here
                            for i in server_chatrooms:
                                if i.name == client_command[1]:
                                    i.join_chatroom(self.name)
                                    self.rooms.append([i.name, 0])
                    case "LISTME":
                        if len(client_command) > 2 and client_command[1] == "REQUEST":
                            for i in server_chatrooms:
                                if client_command[2] == i.name:
                                    users = i.list_connected_users()
                                    self.client_socket.send(users.encode())
                    case "LEAVCR":
                        if len(client_command) > 1:
                            for i in server_chatrooms:
                                if client_command[1] == i.name:
                                    lock.acquire()
                                    left = i.leave_chatroom(self.name)
                                    if left:
                                        self.rooms.remove(client_command[1])
                                        left_msg = self.name + " has disconnected from: " + i.name
                                        i.history.append(left_msg)

                                    else:
                                        self.client_socket.send("Unknown room name\n".encode())
                                    lock.release()
                    case "MSGCHR":
                        if len(client_command) > 1:
                            for i in server_chatrooms:
                                if client_command[1] == i.name:
                                    lock.acquire()
                                    sent_message = self.name + ": " + packet_lines[1]
                                    i.history.append(sent_message) 
                                    lock.release()
                    case "MSGCRS":
                        print("placeholder!")
                    case "DSCTCL":
                        self.client_socket.send("Disconnecting...".encode())
                        lock.acquire()
                        for i in self.rooms:
                            for j in server_chatrooms:
                                if j.name == i:
                                    left = j.leave_chatroom(self.name)
                                    if not left:
                                        print("failed to leave chatroom")
                                        print(j.userlist)
                                    else:
                                        left_msg = self.name + " has disconnected from: " + j.name
                                        j.history.append(left_msg)
                        lock.release()
                        self.rooms = []
                        self.client_socket.close()
                    case other:
                        self.client_socket.send("Server doesn't recognize client command\n".encode())
