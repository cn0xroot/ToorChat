'''
 *  Modified by Salvador Mendoza (salmg.net)
 *  Project: relaying data with Yard Stick One using the ToorChat library
 *  #weekendproject 
 *  More info: https://twitter.com/Netxing/status/1337131398348455936
'''
import sys
from rflib import *
import rflib.chipcon_nic as rfnic
from libtoorchat import *
import os
import time
from threading import Thread

from smartcard.CardType import AnyCardType
from smartcard.CardRequest import CardRequest
from smartcard.util import toHexString, toBytes
from smartcard.System import readers

connection = None
rd = readers()
if len(rd) > 0:
    print(rd)
    connection = rd[2].createConnection()
    connection.connect()
else:
    print("Cannot detect any reader!")
    exit(1)

def thread_run(visual):
    ''' This is our function for the thread '''
    #Thread should run until exit
    while not visual.exit:
        try:
            msg, timestamp = visual.badge.RFrecv()
            toor_message = ToorChatProtocol.parse_message(msg)
            if toor_message != None:
                if toor_message.type == ToorChatProtocol.get_chat_type():
                    visual.message_queue.append(toor_message)
                if toor_message.type == ToorChatProtocol.get_web_request_type():
                    #If we are registered as a server, lets type to make that request
                    if visual.server:
                        visual.request_xid = toor_message.xid
                        ToorChatProtocol.get_web_messages(toor_message.data, visual)
        except ChipconUsbTimeoutException:
            pass

class Visualizer():
    def __init__(self):
        self.badge = RfCat(idx=0)
        self.badge.setModeRX()
        self.protocol = ToorChatProtocol(self.badge)
        self.message_queue = []
        self.user = "None1"
        self.channel = self.protocol.change_channel("0")
        self.frequency = self.protocol.change_frequency("215000000")
        self.request_xid = ToorMessage.get_random_xid()
        self.cardservice = connection

        #This when set to True will kill the thread
        self.exit = False
        self.server = False

    def set_server(self):
        self.server = True

    def start(self):
        self.__start_recv_thread__()
        self.__run__()

    def __start_recv_thread__(self):
        '''This spins off a thread to deal with recving information from the rf device '''
        self.thread = Thread(target=thread_run, args=(self,))
        self.thread.start()

    def __run__(self):
        #in charge to send commands to the card a send its responses over with the yard stick one
        try:
            test ='00A404000E325041592E5359532E4444463031'
            data, sw1, sw2 = self.cardservice.transmit(toBytes(test))
            print(data)
            wait = 0
            old_message = ''
            while True and data:
                if wait == 0:
                    print('Sending data...')
                    print(toHexString(data))
                    self.protocol.send_chat_message(toHexString(data), self.user)
                    wait = 1
                    if old_message:
                            break
                else:
                    if len(self.message_queue) > 0:
                        message = self.message_queue[len(self.message_queue)-1]
                        ms = str(message.data)
                        old_message = ms
                        print('Receiving data: ')
                        print(ms)
                        if ms == 'visa':
                            testaid = '00A4040007A0000000031010'
                            data, sw1, sw2 = self.cardservice.transmit(toBytes(testaid)) 
                            wait = 0

            self.exit = True
            self.stop()

        except KeyboardInterrupt:
            self.exit = True
            self.stop()

    def stop(self):
        pass

if __name__ == '__main__':
    visual = Visualizer()
    visual.start()