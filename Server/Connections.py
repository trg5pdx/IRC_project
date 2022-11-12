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

    def send_message_history(self, queue):
        self.rooms.append(["main", 0])
        if len(queue) > 0:
            for i in queue:
                i = i + "\n"
                self.client_socket.send(i.encode())
                self.rooms[-1][1] += 1
    
    def send_new_messages(self, queue):
        while True:
            # Come back to later and have it find chatroom first
            if len(queue) > self.rooms[0][1]:
                i = self.rooms[0][1]
                while i < len(queue):
                    self.client_socket.send(queue[i].encode())
                    i += 1
                self.rooms[0][1] = i

    def receive_message(self, queue, server_chatrooms, lock):
        response = ""

        with self.client_socket:
            while response != "DSCTSV":
                response = self.client_socket.recv(1024).decode()
                client_command = response.split()

                match client_command[0]:
                    case "HELP":
                        help_message = print_help()
                        self.client_socket.send(help_message.encode())
                    case "LISTCR":
                        rooms = list_rooms(server_chatrooms)
                        self.client_socket.send(rooms.encode())
                    case "JOINCR":
                        if len(client_command) > 1:
                            current_room = client_command[1]
                            # Come back and improve the error handling here
                            for i in server_chatrooms:
                                if i.name == current_room:
                                    i.join_chatroom(self.name)
                                    self.rooms.append(current_room)
                                    print(self.rooms)
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
                    case "DSCTSV":
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
