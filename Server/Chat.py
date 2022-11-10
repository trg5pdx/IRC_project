from socket import *
import threading

class chatroom:
    def __init__(self):
        self.name = ""
        self.history = []
        self.time_created = ""
        self.userlist = []
