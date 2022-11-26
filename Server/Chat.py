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
            if i == self.userlist[-1]:
                user_list += i[1]
            else:
                current = i[1] + ";"
                user_list += current
        return user_list

# Come back and have it throw instead of returning False
def add_new_room(server_chatrooms, lock, name):
    # Checking if a room with that name exists first
    for i in server_chatrooms:
        if name == i.name:
            return False

    lock.acquire()
    new_chatroom = room(name)
    server_chatrooms.append(new_chatroom)
    lock.release()
    return True

def list_rooms(server_chatrooms):
    chat_list = ""

    for i in server_chatrooms:
        current = i.name + ":" + str(len(i.userlist)) + ";"
        chat_list += current

    return chat_list

def list_connected_users(server_chatrooms, room_name):
    for i in server_chatrooms:
        if i.name == room_name:
            return i.list_connected_users()

    return "Room not found\n" 
