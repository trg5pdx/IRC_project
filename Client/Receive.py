# Made by Thomas Gardner, 2022

from socket import *
from enum import Enum
from threading import Thread, Lock
import time
import datetime

Error = Enum('Error', ['Null', 'NotFound', 'NotJoined', 'RoomExists', 
                       'Empty', 'Leave', 'Format', 'Other',])
Cmd = Enum('Cmd', ['Null', 'ListCR', 'Create', 'JoinCR', 'ListME',
                   'LeavCR', 'Msgchr',])
CmdStatus = Enum('CmdStatus', ['Ok','Error'])

def print_chatroom_list(rooms):
    room_list = rooms.split(";")

    output = "List of open chatrooms:\n"
    for i in room_list:
        if len(i) > 0:
            room = i.split(":")
            if room[1] == 1:
                output += room[0] + ": " + room[1] + " user connected\n"
            else:
                output += room[0] + ": " + room[1] + " users connected\n"
    return output 

def print_user_list(users, room):
    user_list = users.split(';')
    output = "Users in " + room + ":\n"
    for i in user_list:
        if i == user_list[-1]:
            output += i
        else:
            output += i + ", "

    return output

def set_username(client_socket):
    while True:
        name = input("Enter your name:\n")
        connection_message = "trgIRC/0.1 CONNCT CLIENT\n"
        connection_message += "USERNAME " + name + "\n"
        
        try:
            client_socket.send(connection_message.encode())
            server_response = client_socket.recv(1024).decode()
            packet_lines = server_response.splitlines() 
            if (packet_lines[0] == "trgIRC/0.1 CONNCT OK" 
                and packet_lines[1] == "MESSAGE"):
                    print(packet_lines[2])
                    return True
            elif packet_lines[0] == "trgIRC/0.1 CONNCT ERROR":
                match packet_lines[1]:
                    case "ERROR NAMEDUP":
                        print("Error, someone is already using that name")
                    case other:
                        print("Error, problem relating to formatting")
        except:
            print("Server has disconnected, closing client...")
            return False


def handle_errors(packet_cmd, packet_status, error_str):
    match packet_status:
        case CmdStatus.Ok:
            print("Something went wrong here")
        case CmdStatus.Error:
            match packet_cmd:
                case Cmd.Create:
                    if error_str == "ROOMEXISTS":
                        return Error.RoomExists
                    else:
                        return Error.Null
                case Cmd.JoinCR:
                    if error_str == "NOTFOUND":
                        return Error.NotFound
                    else:
                        return Error.Null
                case Cmd.LeavCR:
                    if error_str == "NOTFOUND":
                        return Error.NotFound
                    elif error_str == "LEAVE":
                        return Error.Leave
                    else:
                        return Error.Null
                case Cmd.Msgchr:
                    if error_str == "NOTFOUND":
                        return Error.NotFound
                    elif error_str == "NOTJOINED":
                        return Error.NotJoined
                    else:
                        return Error.Null
                case Cmd.ListCR | Cmd.ListME:
                    if error_str == "EMPTY":
                        return Error.Empty
                    elif error_str == "NOTFOUND":
                        return Error.NotFound
                    else:
                        return Error.Null

def set_status(status_code):
    match status_code:
        case "OK" | "RECV":
            return CmdStatus.Ok
        case "ERROR":
            return CmdStatus.Error
        case other:
            return CmdStatus.Error

def receive_server_responses(client_socket, lock):
    while True:
        try:
            packet = client_socket.recv(1024).decode()
            if not packet:
                print("Server has disconnected, closing client...")
                return
            individual_packets = list(filter(None, packet.split("trgIRC/0.1")))
            for i in individual_packets:
                packet_lines = i.splitlines()
                
                packet_cmd = Cmd.Null
                packet_status = CmdStatus.Ok
                msg_header = False
                errors = Error.Null
                username = ""
                msg_time = 0
                room = ""
                message = "" 
                output = "" 

                # Not checking CONNCT as that's handled by the 
                # accept_connections function
                for i in packet_lines:
                    if not msg_header: 
                        line = list(filter(None, i.split()))
                        match line[0]:
                            case "LISTCR":
                                packet_cmd = Cmd.ListCR
                                packet_status = set_status(line[1])
                            case "CREATE":
                                packet_cmd = Cmd.Create
                                packet_status = set_status(line[1])
                            case "JOINCR":
                                packet_cmd = Cmd.JoinCR
                                packet_status = set_status(line[1])
                            case "LISTME":
                                packet_cmd = Cmd.ListME
                                packet_status = set_status(line[1])
                            case "LEAVCR":
                                packet_cmd = Cmd.LeavCR
                                packet_status = set_status(line[1])
                            case "MSGCHR":
                                packet_cmd = Cmd.Msgchr
                                packet_status = set_status(line[1])
                            case "USERNAME":
                                username = line[1]
                            case "ROOM":
                                room = line[1]
                            case "TIME":
                                msg_time = float(line[1])
                            case "ERROR":
                                errors = handle_errors(packet_cmd, 
                                                       packet_status, line[1])
                            case "MESSAGE":
                                msg_header = True
                            case "DSCTSV":
                                lock.acquire()
                                active_connection = False
                                lock.release()
                                print("Server has disconnected, shutting down...")
                                thread.exit()
                    else:
                        message += i
                match packet_status:
                    case CmdStatus.Ok:
                        match packet_cmd:
                            case Cmd.JoinCR:
                                output = "Successfully joined " + room
                            case Cmd.LeavCR:
                                output = "Successfully left " + room
                            case Cmd.ListCR:
                                output = print_chatroom_list(message)
                            case Cmd.ListME:
                                output = print_user_list(message, room)    
                            case Cmd.Msgchr:
                                converted_time = datetime.datetime.fromtimestamp(msg_time)
                                timestamp = converted_time.strftime('%I:%M%p')
                                output = ("[" + timestamp + "]" + "[" + room + 
                                          "]" + username + ": " + message)
                            case Cmd.Create:
                                output = "Successfully created " + room
                    case CmdStatus.Error:
                        match errors:
                            case Error.NotFound:
                                output = "Couldn't find " + room
                            case Error.NotJoined:
                                output = ("Can't send message, not connected to "
                                            + room)
                            case Error.RoomExists:
                                output = room + " already exists"
                            case Error.Leave:
                                output = "Failed to leave " + room
                            case Error.Format:
                                output = "Error with packet format"
                            case Error.Empty:
                                if Cmd.ListCR:
                                    output = "No rooms are open"
                                if Cmd.ListME:
                                    output = "No users connected to this room"
                            case Error.Other:
                                output = "Some error has occured"
                print(output)
        except Exception as e:
            print("An error has occured, closing client, details:")
            print(e)
            lock.acquire()
            active_connection = False
            lock.release()
            return
