#!/usr/bin/env python

######
# qjackctl -s
# saw_converter -r 4243 -s 4242

import json
import socket
import sys
import time
import threading
import subprocess
import math
import mido
import uuid

#import kivy libraries
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.slider import Slider
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.garden.knob import Knob
from kivy.core.window import Window
from kivy.clock import Clock

Window.clearcolor = (0.8, 0.8, 0.9,0)

HOST = 'localhost'
PORT_R = 4242
PORT_S = 4240

#Global variables

objectIDs = [[0],[1,2],[3,4],[5,6],[7,8],[9,10],[11,12],[13,14],[15,16],[17,18],[19,20],[21,22],[23,24],[25,26],range(27,44),range(44,60)]          #Number of objects
Nobjs = len(objectIDs)
object_level = [1]*Nobjs
object_level_list = list()
object_pos = [1]*Nobjs
object_pos_list = list()

renderer = 0
rendererFlag = 0

high_priority_val = 1

pos_range = 180      #Max/min position in degrees

loop_len = 30       #Length of loop in seconds

fname = str(uuid.uuid4()) + '.txt'

metadata = list()
metadataAdjusted = list()
metadataInd = 0
firstLoop = 1

record = 0

def deg2rad(rad):
    deg = (math.pi/180)*rad
    return deg

def start_renderer(renderer):
    #start renderer
    if renderer == 0:
        subprocess.call(['./renderer_all_speakers.sh'])
    elif renderer == 1:
        subprocess.call(['./renderer_5_1.sh'])

def send_receive_json(HOST,PORT_R,PORT_S):
    global firstLoop, metadata, metadataAdjusted, metadataInd, record, object_level_list, object_pos_list
    # UDP socket
    try :
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        print 'Socket created'
    except socket.error,msg :
        print 'Failed to create socket.' + msg[1]
        sys.exit()

    # Bind to local host
    try:
        s.bind((HOST,PORT_R))
    except socket.error, msg:
        print 'Bind failed ' + msg[1]
        sys.exit()

    print 'Socket bind complete'

    t = 0

    #talk with client
    while 1:
        #print time.time() - t
        #t = time.time()
        #time.sleep(0.6) 
        #receive data from client
        d = s.recvfrom(16384)       #Receive UDP packet
        data = d[0]                 #Get data from UDP packet
        addr = d[1]

        newmsg = json.loads(data.strip())       #Parse JSON message

        if firstLoop == 1:          
            metadata.append(newmsg)         #Populate metadata in first loop
            metadataAdjusted.append(newmsg)         #Populate metadata in first loop
            object_level_list.append([1]*Nobjs)
            object_pos_list.append([1]*Nobjs)
        else:                               #Run from 
            if metadataInd < len(metadata):
                if rendererFlag == 0:
                    newmsg = metadata[metadataInd]
                    metadataInd = metadataInd + 1
                    print metadataInd

                if rendererFlag == 1:                       #Only operate on objects if downmix
                    newmsg = metadataAdjusted[metadataInd]
                    metadataInd = metadataInd + 1
                    print metadataInd    
                                       
                    if record == 1:
                        print "recording..."
                        try:
                            for i in range(Nobjs):         #Cycle through object list
                                for j in range(len(objectIDs[i])):
                                    #newmsg['objects'][objectIDs[i][j]]['level'] = object_level[i]
                                    newmsg['objects'][objectIDs[i][j]]['level'] = object_level_list[metadataInd][i]
                                    if newmsg['objects'][objectIDs[i][j]]['type'] == 'plane':
                                        newmsg['objects'][objectIDs[i][j]]['direction']['az'] = object_pos_list[metadataInd][i]
                                    else:
                                        newmsg['objects'][objectIDs[i][j]]['position']['x'] = math.cos(deg2rad(object_pos_list[metadataInd][i]))
                                        newmsg['objects'][objectIDs[i][j]]['position']['y'] = math.sin(deg2rad(object_pos_list[metadataInd][i]))      
                                metadataAdjusted[metadataInd] = newmsg
                        except:
                            print 'Index excceded list size'

        newjsonmsg = json.dumps(newmsg)
        
        #print 'hi'
        s.sendto(newjsonmsg,(HOST,PORT_S))


def monitor_midi():
    with mido.open_input('HDSPMx73554b MIDI 3') as port:
        for message in port:
            if message.type != 'quarter_frame':
                last_time = message
                print last_time

def play_loop(dt):                                              #Start playing at beginning of loop
    global firstLoop, metadataInd, thread
    firstLoop = 0
    metadataInd = 0
    outport = mido.open_output('HDSPMx73554b MIDI 3')
    stop = mido.Message('sysex', data=[127, 127, 6, 1])
    move = mido.Message('sysex', data=[127,127,6,68,6,1,33,0,0,15,0])
    play_msg = mido.Message('sysex', data=[127, 127, 6, 3])
    outport.send(stop)
    outport.send(move)
    outport.send(play_msg)
    


def play_first_loop(dt):                                              #Start playing at beginning of loop
    outport = mido.open_output('HDSPMx73554b MIDI 3')
    stop = mido.Message('sysex', data=[127, 127, 6, 1])
    move = mido.Message('sysex', data=[127,127,6,68,6,1,33,0,0,15,0])
    play_msg = mido.Message('sysex', data=[127, 127, 6, 3])
    outport.send(stop)
    outport.send(move)
    outport.send(play_msg)

renderer_thread = threading.Thread(target=start_renderer,args=[renderer])
if renderer_thread.isAlive():
    print 'Its alive'
renderer_thread.start()


thread = threading.Thread(target=send_receive_json,args=(HOST,PORT_R,PORT_S))
thread.start()

midi_thread = threading.Thread(target=monitor_midi)
midi_thread.start()

class mySlider(GridLayout):

    def __init__(self, **kwargs):
        super(mySlider, self).__init__(**kwargs)

        self.cols = 17
        self.object1_lev_slider = Slider(min=0, max=1,orientation='vertical',value=object_level[0])
        self.object1_pos_slider = Slider(min=-pos_range, max=pos_range,orientation='vertical',value=object_pos[0])
        self.object2_lev_slider = Slider(min=0, max=1,orientation='vertical',value=object_level[1])
        self.object2_pos_slider = Slider(min=-pos_range, max=pos_range,orientation='vertical',value=object_pos[1])
        self.object3_lev_slider = Slider(min=0, max=1,orientation='vertical',value=object_level[2])
        self.object3_pos_slider = Slider(min=-pos_range, max=pos_range,orientation='vertical',value=object_pos[2])
        self.object4_lev_slider = Slider(min=0, max=1,orientation='vertical',value=object_level[3])
        self.object4_pos_slider = Slider(min=-pos_range, max=pos_range,orientation='vertical',value=object_pos[3])
        self.object5_lev_slider = Slider(min=0, max=1,orientation='vertical',value=object_level[4])
        self.object5_pos_slider = Slider(min=-pos_range, max=pos_range,orientation='vertical',value=object_pos[4])
        self.object6_lev_slider = Slider(min=0, max=1,orientation='vertical',value=object_level[5])
        self.object6_pos_slider = Slider(min=-pos_range, max=pos_range,orientation='vertical',value=object_pos[5])
        self.object7_lev_slider = Slider(min=0, max=1,orientation='vertical',value=object_level[6])
        self.object7_pos_slider = Slider(min=-pos_range, max=pos_range,orientation='vertical',value=object_pos[6])
        self.object8_lev_slider = Slider(min=0, max=1,orientation='vertical',value=object_level[7])
        self.object8_pos_slider = Slider(min=-pos_range, max=pos_range,orientation='vertical',value=object_pos[7])
        self.object9_lev_slider = Slider(min=0, max=1,orientation='vertical',value=object_level[8])
        self.object9_pos_slider = Slider(min=-pos_range, max=pos_range,orientation='vertical',value=object_pos[8])
        self.object10_lev_slider = Slider(min=0, max=1,orientation='vertical',value=object_level[9])
        self.object10_pos_slider = Slider(min=-pos_range, max=pos_range,orientation='vertical',value=object_pos[9])
        self.object11_lev_slider = Slider(min=0, max=1,orientation='vertical',value=object_level[10])
        self.object11_pos_slider = Slider(min=-pos_range, max=pos_range,orientation='vertical',value=object_pos[10])
        self.object12_lev_slider = Slider(min=0, max=1,orientation='vertical',value=object_level[11])
        self.object12_pos_slider = Slider(min=-pos_range, max=pos_range,orientation='vertical',value=object_pos[11])
        self.object13_lev_slider = Slider(min=0, max=1,orientation='vertical',value=object_level[12])
        self.object13_pos_slider = Slider(min=-pos_range, max=pos_range,orientation='vertical',value=object_pos[13])
        self.object14_lev_slider = Slider(min=0, max=1,orientation='vertical',value=object_level[13])
        self.object14_pos_slider = Slider(min=-pos_range, max=pos_range,orientation='vertical',value=object_pos[14])
        self.object15_lev_slider = Slider(min=0, max=1,orientation='vertical',value=object_level[14])
        self.object15_pos_slider = Slider(min=-pos_range, max=pos_range,orientation='vertical',value=object_pos[15])
        self.object16_lev_slider = Slider(min=0, max=1,orientation='vertical',value=object_level[15])
        self.object16_pos_slider = Slider(min=-pos_range, max=pos_range,orientation='vertical')
        self.btn_toggle_record = ToggleButton(text = "Read",state = 'normal')
        self.btn_toggle_renderer = ToggleButton(text = "Switch renderer",state = 'normal')
        self.btn_play = Button(text = "PLAY") 
        self.btn_stop = Button(text = "STOP")      
        self.object1_lev_slider.bind(value=self.set_object1_level)
        self.object1_pos_slider.bind(value=self.set_object1_pos)
        self.object2_lev_slider.bind(value=self.set_object2_level)
        self.object2_pos_slider.bind(value=self.set_object2_pos)
        self.object3_lev_slider.bind(value=self.set_object3_level)
        self.object3_pos_slider.bind(value=self.set_object3_pos)
        self.object4_lev_slider.bind(value=self.set_object4_level)
        self.object4_pos_slider.bind(value=self.set_object4_pos)
        self.object5_lev_slider.bind(value=self.set_object5_level)
        self.object5_pos_slider.bind(value=self.set_object5_pos)
        self.object6_lev_slider.bind(value=self.set_object6_level)
        self.object6_pos_slider.bind(value=self.set_object6_pos)
        self.object7_lev_slider.bind(value=self.set_object7_level)
        self.object7_pos_slider.bind(value=self.set_object7_pos)
        self.object8_lev_slider.bind(value=self.set_object8_level)
        self.object8_pos_slider.bind(value=self.set_object8_pos)
        self.object9_lev_slider.bind(value=self.set_object9_level)
        self.object9_pos_slider.bind(value=self.set_object9_pos)
        self.object10_lev_slider.bind(value=self.set_object10_level)
        self.object10_pos_slider.bind(value=self.set_object10_pos)
        self.object11_lev_slider.bind(value=self.set_object11_level)
        self.object11_pos_slider.bind(value=self.set_object11_pos)
        self.object12_lev_slider.bind(value=self.set_object12_level)
        self.object12_pos_slider.bind(value=self.set_object12_pos)
        self.object13_lev_slider.bind(value=self.set_object13_level)
        self.object13_pos_slider.bind(value=self.set_object13_pos)
        self.object14_lev_slider.bind(value=self.set_object14_level)
        self.object14_pos_slider.bind(value=self.set_object14_pos)
        self.object15_lev_slider.bind(value=self.set_object15_level)
        self.object15_pos_slider.bind(value=self.set_object15_pos)
        self.object16_lev_slider.bind(value=self.set_object16_level)
        self.object16_pos_slider.bind(value=self.set_object16_pos)
        self.btn_toggle_record.bind(state=self.switch_record)
        self.btn_toggle_renderer.bind(state=self.switch_renderer)
        self.btn_play.bind(on_press = self.play)
        self.btn_stop.bind(on_press = self.stop)
        self.add_widget(Label(text=''))
        self.add_widget(Label(text='[b]Narrator[/b]',markup = True))
        self.add_widget(Label(text='[b]Isaac[/b]',markup = True))
        self.add_widget(Label(text='[b]Amelia[/b]',markup = True))
        self.add_widget(Label(text='[b]Creature voice[/b]',markup = True))
        self.add_widget(Label(text='[b]Creature feet[/b]',markup = True))
        self.add_widget(Label(text='[b]FX1[/b]',markup = True))
        self.add_widget(Label(text='[b]FX2[/b]',markup = True))
        self.add_widget(Label(text='[b]FX3[/b]',markup = True))
        self.add_widget(Label(text='[b]FX4[/b]',markup = True))
        self.add_widget(Label(text='[b]FX5[/b]',markup = True))
        self.add_widget(Label(text='[b]FX6[/b]',markup = True))
        self.add_widget(Label(text='[b]FX7[/b]',markup = True))
        self.add_widget(Label(text='[b]FX8[/b]',markup = True))
        self.add_widget(Label(text='[b]FX9[/b]',markup = True))
        self.add_widget(Label(text='[b]Music[/b]',markup = True))
        self.add_widget(Label(text='[b]Atmos[/b]',markup = True))
        self.add_widget(Label(text='[b]Level:[/b]',markup = True))
        self.add_widget(self.object1_lev_slider)        
        self.add_widget(self.object2_lev_slider)
        self.add_widget(self.object3_lev_slider)
        self.add_widget(self.object4_lev_slider)
        self.add_widget(self.object5_lev_slider)
        self.add_widget(self.object6_lev_slider)
        self.add_widget(self.object7_lev_slider)
        self.add_widget(self.object8_lev_slider)
        self.add_widget(self.object9_lev_slider)
        self.add_widget(self.object10_lev_slider)
        self.add_widget(self.object11_lev_slider)
        self.add_widget(self.object12_lev_slider)
        self.add_widget(self.object13_lev_slider)
        self.add_widget(self.object14_lev_slider)
        self.add_widget(self.object15_lev_slider)
        self.add_widget(self.object16_lev_slider)
        self.add_widget(Label(text='[b]Position:[/b]',markup = True))
        self.add_widget(self.object1_pos_slider)
        self.add_widget(self.object2_pos_slider)
        self.add_widget(self.object3_pos_slider)
        self.add_widget(self.object4_pos_slider)
        self.add_widget(self.object5_pos_slider)
        self.add_widget(self.object6_pos_slider)
        self.add_widget(self.object7_pos_slider)
        self.add_widget(self.object8_pos_slider)
        self.add_widget(self.object9_pos_slider)
        self.add_widget(self.object10_pos_slider)
        self.add_widget(self.object11_pos_slider)
        self.add_widget(self.object12_pos_slider)
        self.add_widget(self.object13_pos_slider)
        self.add_widget(self.object14_pos_slider)
        self.add_widget(Label(text=''))
        self.add_widget(Label(text=''))
        self.add_widget(Label(text=''))
        self.add_widget(Label(text=''))
        self.add_widget(Label(text=''))
        self.add_widget(Label(text=''))
        self.add_widget(Label(text=''))
        self.add_widget(Label(text=''))
        self.add_widget(self.btn_toggle_record)
        self.add_widget(self.btn_toggle_renderer)
        self.add_widget(self.btn_play)
        self.add_widget(self.btn_stop)

    def set_object1_level(self,instance,val):
        global object_level, metadataInd, object_level_list
        object_level[0] = val
        for i in range(metadataInd,len(object_level_list)):
            object_level_list[i][0] = val        
        print 'Obj1 level set to ' + str(object_level[0])   

    def set_object2_level(self,instance,val):
        global object_level, metadataInd, object_level_list
        object_level[1] = val
        for i in range(metadataInd,len(object_level_list)):
            object_level_list[i][1] = val        
        print 'Obj2 level set to ' + str(object_level[1])


    def set_object3_level(self,instance,val):
        global object_level, metadataInd, object_level_list
        object_level[2] = val
        for i in range(metadataInd,len(object_level_list)):
            object_level_list[i][2] = val        
        print 'Obj3 level set to ' + str(object_level[2])


    def set_object4_level(self,instance,val):
        global object_level, metadataInd, object_level_list
        object_level[3] = val
        for i in range(metadataInd,len(object_level_list)):
            object_level_list[i][3] = val
        print 'Obj4 level set to ' + str(object_level[3])

       
    def set_object5_level(self,instance,val):
        global object_level, metadataInd, object_level_list
        object_level[4] = val
        for i in range(metadataInd,len(object_level_list)):
            object_level_list[i][4] = val
        print 'Obj5 position set to ' + str(object_level[4])


    def set_object6_level(self,instance,val):
        global object_level, metadataInd, object_level_list
        object_level[5] = val
        for i in range(metadataInd,len(object_level_list)):
            object_level_list[i][5] = val
        print 'Obj6 level set to ' + str(object_level[5])



    def set_object7_level(self,instance,val):
        global object_level, metadataInd, object_level_list
        object_level[6] = val
        for i in range(metadataInd,len(object_level_list)):
            object_level_list[i][6] = val
        print 'Obj7 level set to ' + str(object_level[6])



    def set_object8_level(self,instance,val):
        global object_level, metadataInd, object_level_list
        object_level[7] = val
        for i in range(metadataInd,len(object_level_list)):
            object_level_list[i][7] = val
        print 'Obj8 level set to ' + str(object_level[7])



    def set_object9_level(self,instance,val):
        global object_level, metadataInd, object_level_list
        object_level[8] = val
        for i in range(metadataInd,len(object_level_list)):
            object_level_list[i][8] = val        
        print 'Obj4 level set to ' + str(object_level[8])



    def set_object10_level(self,instance,val):
        global object_level, metadataInd, object_level_list
        object_level[9] = val
        for i in range(metadataInd,len(object_level_list)):
            object_level_list[i][9] = val        
        print 'Obj10 level set to ' + str(object_level[9])



    def set_object11_level(self,instance,val):
        global object_level, metadataInd, object_level_list
        object_level[10] = val
        for i in range(metadataInd,len(object_level_list)):
            object_level_list[i][10] = val        
        print 'Obj11 level set to ' + str(object_level[10])


    def set_object12_level(self,instance,val):
        global object_level, metadataInd, object_level_list
        object_level[11] = val
        for i in range(metadataInd,len(object_level_list)):
            object_level_list[i][11] = val        
        print 'Obj12 level set to ' + str(object_level[11])

    def set_object13_level(self,instance,val):
        global object_level, metadataInd, object_level_list
        object_level[12] = val
        for i in range(metadataInd,len(object_level_list)):
            object_level_list[i][13] = val
        print 'Obj13 level set to ' + str(object_level[12]) 

    def set_object14_level(self,instance,val):
        global object_level, metadataInd, object_level_list
        object_level[13] = val
        for i in range(metadataInd,len(object_level_list)):
            object_level_list[i][13] = val
        print 'Obj14 level set to ' + str(object_level[13])

    def set_object15_level(self,instance,val):
        global object_level, metadataInd, object_level_list
        object_level[14] = val
        for i in range(metadataInd,len(object_level_list)):
            object_level_list[i][14] = val    
        print 'Obj15 level set to ' + str(object_level[14])

    def set_object16_level(self,instance,val):
        global object_level, metadataInd, object_level_list
        object_level[15] = val
        for i in range(metadataInd,len(object_level_list)):
            object_level_list[i][15] = val
        print 'Obj16 level set to ' + str(object_level[15])

    def set_object1_pos(self,instance,val):
        global object_pos, metadataInd, object_pos_list
        object_pos[0] = val
        for i in range(metadataInd,len(object_pos_list)):
            object_pos_list[i][0] = val
        print 'Obj1 pos set to ' + str(object_pos[0])

    def set_object2_pos(self,instance,val):
        global object_pos, metadataInd, object_pos_list
        object_pos[1] = val
        for i in range(metadataInd,len(object_pos_list)):
            object_pos_list[i][1] = val
        print 'Obj2 pos set to ' + str(object_pos[1])

    def set_object3_pos(self,instance,val):
        global object_pos, metadataInd, object_pos_list
        object_pos[2] = val
        for i in range(metadataInd,len(object_pos_list)):
            object_pos_list[i][2] = val
        print 'Obj3 pos set to ' + str(object_pos[2])

    def set_object4_pos(self,instance,val):
        global object_pos, metadataInd, object_pos_list
        object_pos[3] = val
        for i in range(metadataInd,len(object_pos_list)):
            object_pos_list[i][3] = val
        print 'Obj4 pos set to ' + str(object_pos[3])        

    def set_object5_pos(self,instance,val):
        global narrator_pos, metadataInd, object_pos_list
        object_pos[4] = val
        for i in range(metadataInd,len(object_pos_list)):
            object_pos_list[i][5] = val
        print 'Obj5 position set to ' + str(object_pos[4])

    def set_object6_pos(self,instance,val):
        global object_pos, metadataInd, object_pos_list
        object_pos[5] = val
        for i in range(metadataInd,len(object_pos_list)):
            object_pos_list[i][6] = val
        print 'Obj6 pos set to ' + str(object_pos[5])

    def set_object7_pos(self,instance,val):
        global object_pos, metadataInd, object_pos_list
        object_pos[6] = val
        for i in range(metadataInd,len(object_pos_list)):
            object_pos_list[i][6] = val
        print 'Obj7 pos set to ' + str(object_pos[6])

    def set_object8_pos(self,instance,val):
        global object_pos, metadataInd, object_pos_list
        object_pos[7] = val
        for i in range(metadataInd,len(object_pos_list)):
            object_pos_list[i][7] = val
        print 'Obj8 pos set to ' + str(object_pos[7])

    def set_object9_pos(self,instance,val):
        global object_pos, metadataInd, object_pos_list
        object_pos[8] = val
        for i in range(metadataInd,len(object_pos_list)):
            object_pos_list[i][8] = val
        print 'Obj4 pos set to ' + str(object_pos[8]) 

    def set_object10_pos(self,instance,val):
        global object_pos, metadataInd, object_pos_list
        object_pos[9] = val
        for i in range(metadataInd,len(object_pos_list)):
            object_pos_list[i][9] = val
        print 'Obj10 pos set to ' + str(object_pos[9])  

    def set_object11_pos(self,instance,val):
        global object_pos, metadataInd, object_pos_list
        object_pos[10] = val
        for i in range(metadataInd,len(object_pos_list)):
            object_pos_list[i][10] = val
        print 'Obj11 pos set to ' + str(object_pos[10])

    def set_object12_pos(self,instance,val):
        global object_pos, metadataInd, object_pos_list
        object_pos[11] = val
        for i in range(metadataInd,len(object_pos_list)):
            object_pos_list[i][11] = val
        print 'Obj12 pos set to ' + str(object_pos[11]) 

    def set_object13_pos(self,instance,val):
        global object_pos, metadataInd, object_pos_list
        object_pos[12] = val
        for i in range(metadataInd,len(object_pos_list)):
            object_pos_list[i][12] = val
        print 'Obj13 pos set to ' + str(object_pos[12]) 

    def set_object14_pos(self,instance,val):
        global object_pos, metadataInd, object_pos_list
        object_pos[13] = val
        for i in range(metadataInd,len(object_pos_list)):
            object_pos_list[i][13] = val
        print 'Obj14 pos set to ' + str(object_pos[13])

    def set_object15_pos(self,instance,val):
        global object_pos, metadataInd, object_pos_list
        object_pos[14] = val
        for i in range(metadataInd,len(object_pos_list)):
            object_pos_list[i][14] = val
        print 'Obj15 pos set to ' + str(object_pos[14]) 

    def set_object16_pos(self,instance,val):
        global object_pos, metadataInd, object_pos_list
        object_pos[15] = val
        for i in range(metadataInd,len(object_pos_list)):
            object_pos_list[i][15] = val
        print 'Obj16 pos set to ' + str(object_pos[15])      
    
    def set_high_priority_level(self,instance,val):
        global high_priority_val
        high_priority_val = val
        for i in range(metadataInd,len(object_pos_list)):
            object_pos_list[i][16] = val
        print 'High priority set to ' + str(high_priority_val)

    def switch_renderer(self,instance,val):
        global renderer_thread 
        global rendererFlag
        #if renderer_thread.isAlive():
        #    renderer_thread.stop()
        if val == 'normal':
            rendererFlag = 0
            renderer_thread = threading.Thread(target=start_renderer,args=[0])
            renderer_thread.start()
        else:
            rendererFlag = 1
            renderer_thread = threading.Thread(target=start_renderer,args=[1])
            renderer_thread.start()


    def switch_record(self,instance,val):
        global record 
       
        if val == 'normal':          
            record = 0
            print record
            self.btn_toggle_record.text = "Reading"
            
        else:
            print "button is up"
            record = 1
            print record
            self.btn_toggle_record.text = "Writing"


    def play(self,instance):
        print 'hi'
        Clock.unschedule(play_loop)
        Clock.schedule_once(play_loop)
        Clock.schedule_interval(play_loop,loop_len)


    def stop(self,instance):
        Clock.unschedule(play_loop)
        outport = mido.open_output('HDSPMx73554b MIDI 3')
        stop_msg = mido.Message('sysex', data=[127, 127, 6, 1])    
        outport.send(stop_msg)

    def write_data(self,dt):
        global object_level, object_pos, fname, object_level_list
        with open(fname,"a") as myfile:
            myfile.write(str(object_level_list) + '\n')
            #myfile.write(str(object_pos) + '\n')

    def update_sliders(self,dt):
        global object_level_list
        if record != 1:
            for i in range(len(object_level_list)):
                'self.object' + str(i+1) + '_lev_slider.value = object_level_list[metadataInd][i]'



class MyApp(App):
    

    def build(self):
        interface = mySlider()
        self.title = ''
        #interface.play()
        Clock.schedule_interval(interface.write_data,0.5)
        Clock.schedule_once(play_first_loop)
        Clock.schedule_interval(play_loop,loop_len)
        #Clock.schedule_interval(interface.update_sliders,0.5)
        return interface

if __name__ == '__main__':

    MyApp().run()