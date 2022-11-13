from socket import *
import threading
import time

class room:
    def __init__(self, name):
        self.name = name
        self.history = []
        self.time_created = time.time() 
        self.userlist = []

    def join_chatroom(self, username):
        self.userlist.append((time.time(), username))
    
    def leave_chatroom(self, username):
        for i in range(len(self.userlist)): 
            if self.userlist[i][1] == username:
                del self.userlist[i]
                return True
        return False

    def list_connected_users(self):
        user_list = ""
        for i in self.userlist:
            # Not printing time atm, come back and print it formatted
            current = i[1] + "\n"
            user_list += current
        return user_list

def add_new_room(server_chatrooms, lock, name):
    lock.acquire()
    new_chatroom = room(name)
    server_chatrooms.append(new_chatroom)
    lock.release()

def list_rooms(server_chatrooms):
    chat_list = ""

    for i in server_chatrooms:
        print(i.userlist)
        current = i.name + ": " + str(len(i.userlist)) + " users connected" + "\n"
        chat_list += current

    return chat_list

def list_connected_users(server_chatrooms, room_name):
    for i in server_chatrooms:
        if i.name == room_name:
            return i.list_connected_users()

    return "Room not found\n" 
