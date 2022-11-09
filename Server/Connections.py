from socket import *
import threading

class connections:
    def __init__(self, client_socket):
        self.name = ""
        self.rooms = []
        self.client_socket = client_socket

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

    def receive_message(self, queue, lock):
        response = ""

        with self.client_socket:
            while response != "/quit":
                response = self.client_socket.recv(1024).decode()
                
                if response == "/quit":
                    self.client_socket.send("disconnecting...".encode())
                    self.client_socket.close()
                else:
                    lock.acquire()
                    queue.append(response)
                    lock.release()
