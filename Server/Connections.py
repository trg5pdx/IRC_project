from socket import *
from Server import *
from Chat import *
import threading

class connections:
    def __init__(self, name, client_socket):
        self.name = name
        self.rooms = []
        self.client_socket = client_socket
        """
        will be used later for allowing a client to send messages without a command
        to a set default chatroom
        """
        self.default_room = ""

    def send_message_history(self, server_chatrooms, room_name):
        for current_room in server_chatrooms:
            if current_room.name == room_name and len(current_room.history) > 0:
                self.rooms.append([room_name, 0])
                for current_message in current_room.history:
                    message = current_message + "\n"
                    self.client_socket.send(message.encode())
                    self.rooms[-1][1] += 1              

    def send_new_messages(self, server_chatrooms):
        while True:
            for rooms in server_chatrooms:
                for user_room in self.rooms:
                    if user_room[0] == rooms.name and len(rooms.history) > user_room[1]:
                        i = user_room[1]
                        while i < len(rooms.history):
                            self.client_socket.send(rooms.history[i].encode())
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
                        rooms = list_rooms(server_chatrooms)
                        self.client_socket.send(rooms.encode())
                    case "CREATE":
                        if len(client_command) > 1:
                            new_room_name = client_command[1]
                            add_new_room(server_chatrooms, lock, new_room_name)
                    case "JOINCR":
                        if len(client_command) > 1:
                            current_room = client_command[1]
                            # Come back and improve the error handling here
                            for i in server_chatrooms:
                                if i.name == current_room:
                                    i.join_chatroom(self.name)
                                    self.rooms.append(current_room)
                            self.send_message_history(server_chatrooms, current_room)
                    case "LEAVCR":
                        if len(client_command) > 1:
                            for i in server_chatrooms:
                                if client_command[1] == i.name:
                                    lock.acquire()
                                    left = i.leave_chatroom(self.name)
                                    if left:
                                        self.rooms.remove(client_command[1])
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
                        lock.release()
                        self.rooms = []
                        self.client_socket.close()
                    case other:
                        self.client_socket.send("Server doesn't recognize client command\n".encode())
