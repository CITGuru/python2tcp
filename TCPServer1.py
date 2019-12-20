import socket
import time
import os
import hashlib
import random

def check_sum(data):
    hash_md5 = hashlib.md5()
    hash_md5.update(data)
    return hash_md5.hexdigest()


class Reciever:

    def __init__(self,win_size, timeout, filename):
        self.w = win_size
        self.completeData = ''
        self.t = timeout
        self.rec_file = ''
        self.base = 0
        self.expec_seqnum = 0
        self.last_ack_sent = -1
        self.soc = socket.socket()
        self.window = [None] * self.w
        self.active_win_packets = self.w
        self.fileclone = filename
        self.logfile = ''
        self.filepointer = 0

    def canAdd(self):  # check if a packet can be added to the send window
        if self.active_win_packets == 0:
            return False
        else:
            return True

    def createResponse(self, seq_num, typ):
        mess_check_sum = check_sum(str(seq_num))
        return str(mess_check_sum) + "/////" + str(seq_num) + "/////" + typ

    def sendAcks(self, packet, counter):
        if counter == -1:
            self.logfile.write(time.ctime(time.time()) + "\t" + str(packet.split('/////')[1]) + "Recieving\n")
            time.sleep(1.7)
            self.soc.send(packet)
            print("Sending ack: ", str(packet.split('/////')[1]) + "NAK\n")
            return
        self.last_ack_sent = int(packet.split("/////")[1]) + counter
        time.sleep(1.7)
        self.soc.send(packet)
        print("Packet sent/")
        self.logfile.write(time.ctime(time.time()) + "\t" + str(packet.split('/////')[1]) + "Recieving\n")
        print("Sending ack: ", str(packet.split('/////')[1]) + "ACK\n")

    def remove(self, poin):
        #print self.window[0], self.window.index(str(poin))
        self.window[self.window.index(poin)] = None
        self.active_win_packets += 1

    def add(self, packet):
        # print(packet, "here", type(packet))
        pack = packet.split('/////')[3]
        
        seqnum = int(packet.split('/////')[1])
        #print packet#, self.window[seqnum % self.w]
        if self.window[seqnum % self.w] == None:
            if seqnum == self.expec_seqnum:
                self.logfile.write(time.ctime(
                    time.time()) + "\t" + str(packet.split('/////')[1]) + "Recieve\n")
                self.active_win_packets -= 1
                self.window[seqnum % self.w] = packet
            elif seqnum > self.expec_seqnum:
                self.logfile.write(time.ctime(
                    time.time()) + "\t" + str(packet.split('/////')[1]) + "Recieving buffer\n")
                self.active_win_packets -= 1
                self.window[seqnum % self.w] = packet

        else:
            print("In buffer!", packet.split('/////')[1])

    def appData(self):
        self.completeData += self.window[self.filepointer].split('/////')[3]
        self.filepointer += 1
        self.remove(self.window[self.filepointer - 1])
        if self.filepointer >= self.w:
            self.filepointer = 0

    def rMessage(self):
        while True:
            pack = self.soc.recv(1024)
            #print pack
            coun = 0
            #print pack.split('\t')
            try:
                print("Receiving packet No.", pack.split('/////')[1])
            except:
                print("Received all lost packets.")

            print(pack.split('/////'))
            if pack == 'Write':
                #print "ya"
                f = open(self.fileclone, 'wb')
                f.write(self.completeData)
                f.close()
                print("Recieved packets written to file")
                break


            elif int(pack.split('/////')[1]) < self.expec_seqnum:
                packet = self.createResponse(self.expec_seqnum-1, "ACK")
                self.sendAcks(packet,self.expec_seqnum-1)

            # elif len(pack.split('/////')) > 1:
            elif int(pack.split('/////')[1]) == self.expec_seqnum:
                nex = 0
                if self.canAdd():
                    try:
                        k = int(pack.split("/////")[4])
                    except:
                        nex = 1
                    if not nex:
                        if int(pack.split("/////")[4]) > 70:
                            self.add(pack)
                            packet = self.createResponse(self.expec_seqnum + coun, "ACK")
                            while self.window[(int(pack.split('/////')[1]) + coun) % self.w] != None:
                                self.appData()
                                coun = coun + 1
                        else:
                            packet = self.createResponse(self.expec_seqnum + coun, "NAK")
                    else:
                        packet = self.createResponse(self.expec_seqnum + coun, "NAK")
                    #print "ggg"
                    self.sendAcks(packet, coun - 1)
                    self.expec_seqnum = self.expec_seqnum + coun
                    print("Updated: ",self.expec_seqnum)
            else:
                # print int(pack.split('/////')[1])
                if self.canAdd():
                    self.add(pack)

    def recieve(self):
        self.logfile = open(os.curdir + '/' + "clientlog.txt", 'wb')
        self.rMessage()
        self.logfile.close()

