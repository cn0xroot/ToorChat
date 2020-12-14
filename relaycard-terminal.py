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
        self.badge = RfCat(idx=1)
        self.badge.setModeRX()
        self.protocol = ToorChatProtocol(self.badge)
        self.message_queue = []
        self.user = "None2"
        self.channel = self.protocol.change_channel("0")
        self.frequency = self.protocol.change_frequency("215000000")
        self.request_xid = ToorMessage.get_random_xid()

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
        #in charge to receive the responses and request the next commands to the card 
        try:
            self.last_message_index = 0
            a = 0
            old_message = ''
            print('Waiting for mgs!')
            while a < 2:
                if len(self.message_queue) > 0:
                    message = self.message_queue[len(self.message_queue)-1]
                    ms = str(message.data)

                    if ms == old_message :
                        continue

                    old_message = ms
                    print('Receiving data: ')
                    print(ms)
                    if a == 0:
                        print('Requesting visa AID & sending')
                        self.protocol.send_chat_message('visa', self.user)
                    a += 1

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
