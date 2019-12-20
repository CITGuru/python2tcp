import socket
import time
import os
import hashlib
import random


def check_sum(data):
    hash_md5 = hashlib.md5()
    hash_md5.update(data)
    return hash_md5.hexdigest()


class Sender:

    def __init__(self, win_size, timeout, num_packets, filename):
        self.w = win_size
        self.t = timeout
        self.n = num_packets
        self.filename = filename
        self.cur_seq = 0
        self.active_spaces = self.w
        self.window = win_size * [None]
        self.soc = socket.socket()
        self.last_sent_seqnum = -1
        self.last_ack_seqnum = -1
        self.logfile = ''

    def canAdd(self):  # check if a packet can be added to the send window
        if self.active_spaces == 0:
            return False
        else:
            return True

    def sendPack(self, pack, conn):  # function to send the packet through the socket
        time.sleep(1.5)
        conn.send(pack)
        print("Sending packet No.", int(pack.split('/////')[1]))
        print(pack.split('/////'))
        self.logfile.write(time.ctime(time.time()) + "\t" +
                           str(pack.split('/////')[1]) + "Sending\n")

    def add(self, pack, conn):  # add a packet to the send window
        self.last_sent_seqnum = self.cur_seq
        self.cur_seq += 1
        self.window[self.w - self.active_spaces] = pack
        self.active_spaces -= 1
        self.sendPack(pack, conn)

    def resend(self, conn):  # function to resend packet if lost
        cur_num = 0
        while cur_num < self.w - self.active_spaces:
            print("Resending: ", str(self.window[cur_num].split('/////')[1]))
            self.logfile.write(time.ctime(
                time.time()) + "\t" + str(self.window[cur_num].split('/////')[1]) + "Re-sending\n")
            time.sleep(1.4)
            temp = self.window[cur_num].split('/////')
            self.window[cur_num] = temp[0] + '/////' + temp[1] + '/////' + temp[2] + '/////' + temp[3] + '/////' + str(
                random.randint(70, 100))
            print(self.window[cur_num].split('/////'))

            conn.send(self.window[cur_num])
            cur_num += 1
        print("Done resending")

    def makePack(self, num, pac):  # Create a packet
        sequence_number = num
        file_check_sum = check_sum(pac)
        pack_size = len(pac)
        prob = random.randint(0, 100)
        packet = str(file_check_sum) + '/////' + str(sequence_number) + \
                 '/////' + str(pack_size) + '/////' + \
                 str(pac) + '/////' + str(prob)
        return packet

    def divide(self, data, num):  # create packets from datas
        lis = []
        while data:
            lis.append(data[:num])
            data = data[num:]
        return lis

    def acc_Acks(self, conn):  # check if all the sent packets have been ACKed
        print("Checking if packets have been ACKed")
        try:
            packet = (conn.recv(1024)).decode("utf-8")
            print("ACKed packets recieved")
        except:
            print('Connection lost due to timeout!')
            self.logfile.write(time.ctime(time.time()) + "\t" + str(self.last_ack_seqnum + 1) + "Lost TImeout")
            return 0
        if packet.split('/////')[2] == "NAK":
            return 0
        
        try:
            packet_recieved = int(packet.split('/////')[1])
        except ValueError:
            packet_recieved = packet.split('/////')
            packet_recieved.reverse()
            packet_recieved = packet_recieved[1]

        print("Recieved Ack number: ", packet_recieved)
        print("\n")            
        if int(packet_recieved) == self.last_ack_seqnum + 1:
            self.last_ack_seqnum = int(packet_recieved)
            self.window.pop(0)
            self.window.append(None)
            self.active_spaces += 1
            return 1

        elif int(packet_recieved) > self.last_ack_seqnum + 1:
            k = self.last_ack_seqnum
            while (k < int(packet_recieved)):
                self.window.pop(0)
                self.window.append(None)
                self.active_spaces += 1
                k = k + 1
            self.last_ack_seqnum = int(packet_recieved)
            print("Last ACK No: ",self.last_ack_seqnum)
            return 1

        else:
            return 0

    def sendmess(self, pack_list, length, conn):  # send the messages till all packets are sent
        cur_pack = 0
        while (cur_pack < length or self.last_ack_seqnum != length - 1):
            while self.canAdd() and cur_pack != length:
                pack = self.makePack(cur_pack, pack_list[cur_pack])
                cur_pack = cur_pack + 1
                self.add(pack, conn)
            if self.acc_Acks(conn) == 0:
                time.sleep(1.7)
                self.resend(conn)

        time.sleep(1.7)
        print("Finished sending file")
        time.sleep(1.7)
        conn.send("Write")

    def run(self, conn):  # run this to send packets from the file
        try:
            fil = open(self.filename, 'rb')
            data = fil.read()
            pack_list = self.divide(data, 7)
            fil.close()
        except IOError:
            print("No such file exists")
        fname = "servlog.txt"
        self.logfile = open(os.curdir + "/" + fname, "w+")
        l = len(pack_list)
        print("Sending pack list of", l)
        self.sendmess(pack_list, l, conn)
        self.logfile.close()


