#!/usr/bin/env python

######
# qjackctl -s
# saw_converter -r 4243 -s 4242

################################
# For clip 1:
# FX 8 = woodpecker
# FX 9 = croaking

import json
import socket
import sys
import time
import threading
import subprocess
import math
import mido
import uuid
import random
import os

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

Window.clearcolor = (0.5, 0.5, 0.5,0)

HOST = 'localhost'
PORT_R = 4242
PORT_S = 4240

#Global variables

objectIDs = [[1,2],[5,6],[7,8],[9,10,11,12],[15,16],[19,20],range(27,44),range(23,27) + range(44,60)]          #Number of objects
Nobjs = len(objectIDs)


pos_range = 45      #Max/min position in degrees

start_time = 75
loop_len = 20       #Length of loop in seconds

object_level = list()   #Generate some random initial values
for n in range(Nobjs):
    object_level.append(random.random())

object_pos = list()
for n in range(Nobjs):
    object_pos.append((random.random()-0.5) * (2*pos_range))


object_level_list = list()
object_pos_list = list()

renderer = 0
rendererFlag = 0

high_priority_val = 1


folder_name = str(uuid.uuid4())
os.mkdir(folder_name)
file_name = 0

metadata = list()
metadataAdjusted = list()
metadataInd = 0
firstLoop = 1

record = 0
write_mode = 0

def remap(val, old_min, old_max, new_min, new_max):
    return (((val - old_min)*(new_max - new_min)) / (old_max - old_min)) + new_min

def deg2rad(rad):
    deg = (math.pi/180)*rad
    return deg

def start_renderer(renderer):
    #start renderer
    if renderer == 0:
        subprocess.call(['./renderer_all_speakers.sh'])
    elif renderer == 1:
        subprocess.call(['./renderer_2_0.sh'])

def send_receive_json(HOST,PORT_R,PORT_S):
    global firstLoop, metadata, metadataAdjusted, metadataInd, record, object_level_list, object_pos_list, object_level, object_pos
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
        #print data
        newmsg = json.loads(data.strip())       #Parse JSON message

        if firstLoop == 1:

            for i in range(Nobjs):         #Fix heigth for forest scene
                for j in range(len(objectIDs[i])):
                        if newmsg['objects'][objectIDs[i][j]]['type'] == 'plane':
                            height = math.sin(float(newmsg['objects'][objectIDs[i][j]]['direction']['el']))
                        else:
                            height = float(newmsg['objects'][objectIDs[i][j]]['position']['z'])
                            if 1 <= height <= 2:
                                #Remap a height between 1 - 2 to a new value between 0 and 2
                                newmsg['objects'][objectIDs[i][j]]['position']['z'] = remap(height, 1, 2, 0, 2)
                            elif -2 <= height < 1:
                                newmsg['objects'][objectIDs[i][j]]['position']['z'] = remap(height, -2, 1, -2, 0)
                                #Remap a height between -1 - 1 to a new value between -2 and 0

                            
            metadata.append(newmsg)         #Populate metadata in first loop
            #print data
            metadataAdjusted.append(newmsg)         #Populate metadata in first loop
            object_level_list.append(list(object_level))
            #print object_level
            object_pos_list.append(list(object_pos))
        else:                               #Run from   
            if metadataInd < len(metadata):
                if rendererFlag == 0:
                    newmsg = metadata[metadataInd]
                    metadataInd = metadataInd + 1
                    #print metadataInd

                if rendererFlag == 1:                       #Only operate on objects if downmix
                    newmsg = metadataAdjusted[metadataInd]
                    metadataInd = metadataInd + 1
                    #print metadataInd                       
                    #print "recording..."
                    try:                                #Sometimes the sync goes out and inedx exceeds dimensions of object_level_list...
                        #print object_level_list
                        for i in range(Nobjs):         #Cycle through object list
                            for j in range(len(objectIDs[i])):
                                #newmsg['objects'][objectIDs[i][j]]['level'] = object_level[i]
                                newmsg['objects'][objectIDs[i][j]]['level'] = object_level_list[metadataInd][i]
                                if i < 27:                  #Don't change position of atmos and music (they have ids < 27)
                                    if newmsg['objects'][objectIDs[i][j]]['type'] == 'plane':
                                        newmsg['objects'][objectIDs[i][j]]['direction']['az'] = object_pos_list[metadataInd][i]
                                    else:
                                        newmsg['objects'][objectIDs[i][j]]['position']['x'] = math.cos(deg2rad(object_pos_list[metadataInd][i]))
                                        newmsg['objects'][objectIDs[i][j]]['position']['y'] = math.sin(deg2rad(object_pos_list[metadataInd][i]))      
                                metadataAdjusted[metadataInd] = newmsg
                                #print object_level_list[metadataInd][i]
                    except:                         #...if this happens, use the previous frame's metadata
                        print 'Index excceded list size'
                        for i in range(Nobjs):         #Cycle through object list
                            for j in range(len(objectIDs[i])):
                                #newmsg['objects'][objectIDs[i][j]]['level'] = object_level[i]
                                newmsg['objects'][objectIDs[i][j]]['level'] = object_level_list[metadataInd-1][i]
                                if i < 27:
                                    if newmsg['objects'][objectIDs[i][j]]['type'] == 'plane':
                                        newmsg['objects'][objectIDs[i][j]]['direction']['az'] = object_pos_list[metadataInd-1][i]
                                    else:
                                        newmsg['objects'][objectIDs[i][j]]['position']['x'] = math.cos(deg2rad(object_pos_list[metadataInd-1][i]))
                                        newmsg['objects'][objectIDs[i][j]]['position']['y'] = math.sin(deg2rad(object_pos_list[metadataInd-1][i]))      
                                #metadataAdjusted[metadataInd - 1] = newmsg

        newjsonmsg = json.dumps(newmsg)
        
        #print 'hi'
        s.sendto(newjsonmsg,(HOST,PORT_S))


def monitor_midi():             #Monitor new midi messages
    with mido.open_input('HDSPMx73554b MIDI 3') as port:
        for message in port:
            if message.type != 'quarter_frame':
                last_time = message
                print last_time

def play_loop(dt):                                              #Start playing at beginning of loop
    global firstLoop, metadataInd, thread, start_time
    firstLoop = 0
    metadataInd = 0
    outport = mido.open_output('HDSPMx73554b MIDI 3')
    stop = mido.Message('sysex', data=[127, 127, 6, 1])
    move = mido.Message('sysex', data=[127,127,6,68,6,1,33,0,start_time,0,0])
    play_msg = mido.Message('sysex', data=[127, 127, 6, 3])
    outport.send(stop)
    outport.send(move)
    outport.send(play_msg)
    


def play_first_loop(dt):                                              #Start playing at beginning of loop
    outport = mido.open_output('HDSPMx73554b MIDI 3')
    stop = mido.Message('sysex', data=[127, 127, 6, 1])
    move = mido.Message('sysex', data=[127,127,6,68,6,1,33,0,start_time,0,0])
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

#midi_thread = threading.Thread(target=monitor_midi)
#midi_thread.start()

class mySlider(GridLayout):

    def __init__(self, **kwargs):
        super(mySlider, self).__init__(**kwargs)

        self.cols = 9
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
        # self.object9_lev_slider = Slider(min=0, max=1,orientation='vertical',value=object_level[8])
        # self.object9_pos_slider = Slider(min=-pos_range, max=pos_range,orientation='vertical',value=object_pos[8])
        # self.object10_lev_slider = Slider(min=0, max=1,orientation='vertical',value=object_level[9])
        # self.object10_pos_slider = Slider(min=-pos_range, max=pos_range,orientation='vertical',value=object_pos[9])
        # self.object11_lev_slider = Slider(min=0, max=1,orientation='vertical',value=object_level[10])
        # self.object11_pos_slider = Slider(min=-pos_range, max=pos_range,orientation='vertical',value=object_pos[10])
        # self.object12_lev_slider = Slider(min=0, max=1,orientation='vertical',value=object_level[11])
        # self.object12_pos_slider = Slider(min=-pos_range, max=pos_range,orientation='vertical',value=object_pos[11])
        # self.object13_lev_slider = Slider(min=0, max=1,orientation='vertical',value=object_level[12])
        # self.object13_pos_slider = Slider(min=-pos_range, max=pos_range,orientation='vertical',value=object_pos[13])
        # self.object14_lev_slider = Slider(min=0, max=1,orientation='vertical',value=object_level[13])
        # self.object14_pos_slider = Slider(min=-pos_range, max=pos_range,orientation='vertical',value=object_pos[14])
        # self.object15_lev_slider = Slider(min=0, max=1,orientation='vertical',value=object_level[14])
        # self.object15_pos_slider = Slider(min=-pos_range, max=pos_range,orientation='vertical',value=object_pos[15])
        # self.object16_lev_slider = Slider(min=0, max=1,orientation='vertical',value=object_level[15])
        # self.object16_pos_slider = Slider(min=-pos_range, max=pos_range,orientation='vertical')
        self.btn_toggle_record = ToggleButton(text = "Reading", state = 'normal')
        self.btn_toggle_record_mode = ToggleButton(text = "Write to all", state = 'normal')
        self.btn_toggle_renderer = ToggleButton(text = "Reference",state = 'normal')
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
        # self.object9_lev_slider.bind(value=self.set_object9_level)
        # self.object9_pos_slider.bind(value=self.set_object9_pos)
        # self.object10_lev_slider.bind(value=self.set_object10_level)
        # self.object10_pos_slider.bind(value=self.set_object10_pos)
        # self.object11_lev_slider.bind(value=self.set_object11_level)
        # self.object11_pos_slider.bind(value=self.set_object11_pos)
        # self.object12_lev_slider.bind(value=self.set_object12_level)
        # self.object12_pos_slider.bind(value=self.set_object12_pos)
        # self.object13_lev_slider.bind(value=self.set_object13_level)
        # self.object13_pos_slider.bind(value=self.set_object13_pos)
        # self.object14_lev_slider.bind(value=self.set_object14_level)
        # self.object14_pos_slider.bind(value=self.set_object14_pos)
        # self.object15_lev_slider.bind(value=self.set_object15_level)
        # self.object15_pos_slider.bind(value=self.set_object15_pos)
        # self.object16_lev_slider.bind(value=self.set_object16_level)
        # self.object16_pos_slider.bind(value=self.set_object16_pos)
        self.btn_toggle_record.bind(state=self.switch_record)
        self.btn_toggle_record_mode.bind(state=self.switch_record_mode)
        self.btn_toggle_renderer.bind(state=self.switch_renderer)
        self.btn_play.bind(on_press = self.play)
        self.btn_stop.bind(on_press = self.stop)
        self.add_widget(Label(text=''))
        #self.add_widget(Label(text='[b]Narrator[/b]',markup = True))
        self.add_widget(Label(text='[b]Isaac[/b]',markup = True))
        #self.add_widget(Label(text='[b]Amelia[/b]',markup = True))
        self.add_widget(Label(text='[b]Creature voice[/b]',markup = True))
        self.add_widget(Label(text='[b]Creature feet[/b]',markup = True))
        self.add_widget(Label(text='[b]Feet landing[/b]',markup = True))
        #self.add_widget(Label(text='[b]FX2[/b]',markup = True))
        #self.add_widget(Label(text='[b]FX3[/b]',markup = True))
        #self.add_widget(Label(text='[b]FX4[/b]',markup = True))
        #self.add_widget(Label(text='[b]FX5[/b]',markup = True))
        #self.add_widget(Label(text='[b]FX6[/b]',markup = True))
        #self.add_widget(Label(text='[b]FX7[/b]',markup = True))
        self.add_widget(Label(text='[b]Creaking[/b]',markup = True))
        self.add_widget(Label(text='[b]Bird[/b]',markup = True))
        self.add_widget(Label(text='[b]Music[/b]',markup = True))
        self.add_widget(Label(text='[b]Atmos[/b]',markup = True))
        # self.add_widget(Label(text='[b]Reverb[/b]',markup = True))

        self.add_widget(Label(text='[b]Level:[/b]',markup = True))
        self.add_widget(self.object1_lev_slider)        
        self.add_widget(self.object2_lev_slider)
        self.add_widget(self.object3_lev_slider)
        self.add_widget(self.object4_lev_slider)
        self.add_widget(self.object5_lev_slider)
        self.add_widget(self.object6_lev_slider)
        self.add_widget(self.object7_lev_slider)
        self.add_widget(self.object8_lev_slider)
        # self.add_widget(self.object9_lev_slider)
        # self.add_widget(self.object10_lev_slider)
        # self.add_widget(self.object11_lev_slider)
        # self.add_widget(self.object12_lev_slider)
        # self.add_widget(self.object13_lev_slider)
        # self.add_widget(self.object14_lev_slider)
        # self.add_widget(self.object15_lev_slider)
        # self.add_widget(self.object16_lev_slider)

        self.add_widget(Label(text='[b]Position:[/b]',markup = True))
        self.add_widget(self.object1_pos_slider)
        self.add_widget(self.object2_pos_slider)
        self.add_widget(self.object3_pos_slider)
        self.add_widget(self.object4_pos_slider)
        self.add_widget(self.object5_pos_slider)
        self.add_widget(self.object6_pos_slider)
        # self.add_widget(self.object7_pos_slider)
        # self.add_widget(self.object8_pos_slider)
        # self.add_widget(self.object9_pos_slider)
        # self.add_widget(self.object10_pos_slider)
        # self.add_widget(self.object11_pos_slider)
        # self.add_widget(self.object12_pos_slider)
        # self.add_widget(self.object13_pos_slider)
        # self.add_widget(self.object14_pos_slider)
        self.add_widget(Label(text=''))
        self.add_widget(Label(text=''))
        # self.add_widget(Label(text=''))

        self.add_widget(self.btn_toggle_record_mode)
        self.add_widget(Label(text=''))

        self.add_widget(self.btn_toggle_record)
        self.add_widget(self.btn_toggle_renderer)
        self.add_widget(self.btn_play)
        self.add_widget(self.btn_stop)

    def set_object1_level(self,instance,val):
        global metadataInd, object_level_list, record, write_mode
        #print object_level_list
        if record == 1:
            if write_mode == 1:                                 #Write to end
                for i in range(metadataInd,len(object_level_list)):
                    object_level_list[i][0] = val
                    #print object_level_list[i]
                    print 'Writing to end'
            else:
                for i in range(0,len(object_level_list)):       #Write to all
                    object_level_list[i][0] = val
                    #print object_level_list[i]
                    print 'Writing to all'

    def set_object2_level(self,instance,val):
        global metadataInd, object_level_list, record, write_mode
        if record == 1:
            if write_mode == 1:                                 #Write to end
                for i in range(metadataInd,len(object_level_list)):
                    object_level_list[i][1] = val
                    print object_level_list[i]
            else:
                for i in range(0,len(object_level_list)):       #Write to all
                    object_level_list[i][1] = val
                    print object_level_list[i] 


    def set_object3_level(self,instance,val):
        global metadataInd, object_level_list, record, write_mode
        if record == 1:
            if write_mode == 1:                                 #Write to end
                for i in range(metadataInd,len(object_level_list)):
                    object_level_list[i][2] = val
                    print object_level_list[i]
            else:
                for i in range(0,len(object_level_list)):       #Write to all
                    object_level_list[i][2] = val
                    print object_level_list[i] 


    def set_object4_level(self,instance,val):
        global metadataInd, object_level_list, record, write_mode
        if record == 1:
            if write_mode == 1:                                 #Write to end
                for i in range(metadataInd,len(object_level_list)):
                    object_level_list[i][3] = val
                    print object_level_list[i]
            else:
                for i in range(0,len(object_level_list)):       #Write to all
                    object_level_list[i][3] = val
                    print object_level_list[i] 

       
    def set_object5_level(self,instance,val):
        global metadataInd, object_level_list, record, write_mode
        if record == 1:
            if write_mode == 1:                                 #Write to end
                for i in range(metadataInd,len(object_level_list)):
                    object_level_list[i][4] = val
                    print object_level_list[i]
            else:
                for i in range(0,len(object_level_list)):       #Write to all
                    object_level_list[i][4] = val
                    print object_level_list[i] 


    def set_object6_level(self,instance,val):
        global metadataInd, object_level_list, record, write_mode
        if record == 1:
            if write_mode == 1:                                 #Write to end
                for i in range(metadataInd,len(object_level_list)):
                    object_level_list[i][5] = val
                    print object_level_list[i]
            else:
                for i in range(0,len(object_level_list)):       #Write to all
                    object_level_list[i][5] = val
                    print object_level_list[i] 



    def set_object7_level(self,instance,val):
        global metadataInd, object_level_list, record, write_mode
        if record == 1:
            if write_mode == 1:                                 #Write to end
                for i in range(metadataInd,len(object_level_list)):
                    object_level_list[i][6] = val
                    print object_level_list[i]
            else:
                for i in range(0,len(object_level_list)):       #Write to all
                    object_level_list[i][6] = val
                    print object_level_list[i]



    def set_object8_level(self,instance,val):
        global metadataInd, object_level_list, record, write_mode
        if record == 1:
            if write_mode == 1:                                 #Write to end
                for i in range(metadataInd,len(object_level_list)):
                    object_level_list[i][7] = val
                    print object_level_list[i]
            else:
                for i in range(0,len(object_level_list)):       #Write to all
                    object_level_list[i][7] = val
                    print object_level_list[i] 



    def set_object9_level(self,instance,val):
        global metadataInd, object_level_list, record, write_mode
        if record == 1:
            if write_mode == 1:                                 #Write to end
                for i in range(metadataInd,len(object_level_list)):
                    object_level_list[i][8] = val
                    print object_level_list[i]
            else:
                for i in range(0,len(object_level_list)):       #Write to all
                    object_level_list[i][8] = val
                    print object_level_list[i] 



    def set_object10_level(self,instance,val):
        global metadataInd, object_level_list, record, write_mode
        if record == 1:
            if write_mode == 1:                                 #Write to end
                for i in range(metadataInd,len(object_level_list)):
                    object_level_list[i][9] = val
                    print object_level_list[i]
            else:
                for i in range(0,len(object_level_list)):       #Write to all
                    object_level_list[i][9] = val
                    print object_level_list[i] 



    def set_object11_level(self,instance,val):
        global metadataInd, object_level_list, record, write_mode
        if record == 1:
            if write_mode == 1:                                 #Write to end
                for i in range(metadataInd,len(object_level_list)):
                    object_level_list[i][10] = val
                    print object_level_list[i]
            else:
                for i in range(0,len(object_level_list)):       #Write to all
                    object_level_list[i][10] = val
                    print object_level_list[i] 


    def set_object12_level(self,instance,val):
        global metadataInd, object_level_list, record, write_mode
        if record == 1:
            if write_mode == 1:                                 #Write to end
                for i in range(metadataInd,len(object_level_list)):
                    object_level_list[i][11] = val
                    print object_level_list[i]
            else:
                for i in range(0,len(object_level_list)):       #Write to all
                    object_level_list[i][11] = val
                    print object_level_list[i] 

    def set_object13_level(self,instance,val):
        global metadataInd, object_level_list, record, write_mode
        if record == 1:
            if write_mode == 1:                                 #Write to end
                for i in range(metadataInd,len(object_level_list)):
                    object_level_list[i][12] = val
                    print object_level_list[i]
            else:
                for i in range(0,len(object_level_list)):       #Write to all
                    object_level_list[i][12] = val
                    print object_level_list[i] 

    def set_object14_level(self,instance,val):
        global metadataInd, object_level_list, record, write_mode
        if record == 1:
            if write_mode == 1:                                 #Write to end
                for i in range(metadataInd,len(object_level_list)):
                    object_level_list[i][13] = val
                    print object_level_list[i]
            else:
                for i in range(0,len(object_level_list)):       #Write to all
                    object_level_list[i][13] = val
                    print object_level_list[i] 

    def set_object15_level(self,instance,val):
        global metadataInd, object_level_list, record, write_mode
        if record == 1:
            if write_mode == 1:                                 #Write to end
                for i in range(metadataInd,len(object_level_list)):
                    object_level_list[i][14] = val
                    print object_level_list[i]
            else:
                for i in range(0,len(object_level_list)):       #Write to all
                    object_level_list[i][14] = val
                    print object_level_list[i]

    def set_object16_level(self,instance,val):
        global metadataInd, object_level_list, record, write_mode
        if record == 1:
            if write_mode == 1:                                 #Write to end
                for i in range(metadataInd,len(object_level_list)):
                    object_level_list[i][15] = val
                    print object_level_list[i]
            else:
                for i in range(0,len(object_level_list)):       #Write to all
                    object_level_list[i][15] = val
                    print object_level_list[i]

    def set_object1_pos(self,instance,val):
        global metadataInd, object_pos_list, record, write_mode
        if record == 1:
            if write_mode == 1:                                 #Write to end
                for i in range(metadataInd,len(object_pos_list)):
                    object_pos_list[i][0] = val
                    print object_pos_list[i]
            else:
                for i in range(0,len(object_pos_list)):       #Write to all
                    object_pos_list[i][0] = val
                    print object_pos_list[i]

    def set_object2_pos(self,instance,val):
        global metadataInd, object_pos_list, record, write_mode
        if record == 1:
            if write_mode == 1:                                 #Write to end
                for i in range(metadataInd,len(object_pos_list)):
                    object_pos_list[i][1] = val
                    print object_pos_list[i]
            else:
                for i in range(0,len(object_pos_list)):       #Write to all
                    object_pos_list[i][1] = val
                    print object_pos_list[i] 

    def set_object3_pos(self,instance,val):
        global metadataInd, object_pos_list, record, write_mode
        if record == 1:
            if write_mode == 1:                                 #Write to end
                for i in range(metadataInd,len(object_pos_list)):
                    object_pos_list[i][2] = val
                    print object_pos_list[i]
            else:
                for i in range(0,len(object_pos_list)):       #Write to all
                    object_pos_list[i][2] = val
                    print object_pos_list[i]

    def set_object4_pos(self,instance,val):
        global metadataInd, object_pos_list, record, write_mode
        if record == 1:
            if write_mode == 1:                                 #Write to end
                for i in range(metadataInd,len(object_pos_list)):
                    object_pos_list[i][3] = val
                    print object_pos_list[i]
            else:
                for i in range(0,len(object_pos_list)):       #Write to all
                    object_pos_list[i][3] = val
                    print object_pos_list[i]        

    def set_object5_pos(self,instance,val):
        global metadataInd, object_pos_list, record, write_mode
        if record == 1:
            if write_mode == 1:                                 #Write to end
                for i in range(metadataInd,len(object_pos_list)):
                    object_pos_list[i][4] = val
                    print object_pos_list[i]
            else:
                for i in range(0,len(object_pos_list)):       #Write to all
                    object_pos_list[i][4] = val
                    print object_pos_list[i]

    def set_object6_pos(self,instance,val):
        global metadataInd, object_pos_list, record, write_mode
        if record == 1:
            if write_mode == 1:                                 #Write to end
                for i in range(metadataInd,len(object_pos_list)):
                    object_pos_list[i][5] = val
                    print object_pos_list[i]
            else:
                for i in range(0,len(object_pos_list)):       #Write to all
                    object_pos_list[i][5] = val
                    print object_pos_list[i] 

    def set_object7_pos(self,instance,val):
        global metadataInd, object_pos_list, record, write_mode
        if record == 1:
            if write_mode == 1:                                 #Write to end
                for i in range(metadataInd,len(object_pos_list)):
                    object_pos_list[i][6] = val
                    print object_pos_list[i]
            else:
                for i in range(0,len(object_pos_list)):       #Write to all
                    object_pos_list[i][6] = val
                    print object_pos_list[i] 

    def set_object8_pos(self,instance,val):
        global metadataInd, object_pos_list, record, write_mode
        if record == 1:
            if write_mode == 1:                                 #Write to end
                for i in range(metadataInd,len(object_pos_list)):
                    object_pos_list[i][7] = val
                    print object_pos_list[i]
            else:
                for i in range(0,len(object_pos_list)):       #Write to all
                    object_pos_list[i][7] = val
                    print object_pos_list[i]

    def set_object9_pos(self,instance,val):
        global metadataInd, object_pos_list, record, write_mode
        if record == 1:
            if write_mode == 1:                                 #Write to end
                for i in range(metadataInd,len(object_pos_list)):
                    object_pos_list[i][8] = val
                    print object_pos_list[i]
            else:
                for i in range(0,len(object_pos_list)):       #Write to all
                    object_pos_list[i][8] = val
                    print object_pos_list[i]  

    def set_object10_pos(self,instance,val):
        global metadataInd, object_pos_list, record, write_mode
        if record == 1:
            if write_mode == 1:                                 #Write to end
                for i in range(metadataInd,len(object_pos_list)):
                    object_pos_list[i][9] = val
                    print object_pos_list[i]
            else:
                for i in range(0,len(object_pos_list)):       #Write to all
                    object_pos_list[i][9] = val
                    print object_pos_list[i]  

    def set_object11_pos(self,instance,val):
        global metadataInd, object_pos_list, record, write_mode
        if record == 1:
            if write_mode == 1:                                 #Write to end
                for i in range(metadataInd,len(object_pos_list)):
                    object_pos_list[i][10] = val
                    print object_pos_list[i]
            else:
                for i in range(0,len(object_pos_list)):       #Write to all
                    object_pos_list[i][10] = val
                    print object_pos_list[i] 

    def set_object12_pos(self,instance,val):
        global metadataInd, object_pos_list, record, write_mode
        if record == 1:
            if write_mode == 1:                                 #Write to end
                for i in range(metadataInd,len(object_pos_list)):
                    object_pos_list[i][11] = val
                    print object_pos_list[i]
            else:
                for i in range(0,len(object_pos_list)):       #Write to all
                    object_pos_list[i][11] = val
                    print object_pos_list[i]  

    def set_object13_pos(self,instance,val):
        global metadataInd, object_pos_list, record, write_mode
        if record == 1:
            if write_mode == 1:                                 #Write to end
                for i in range(metadataInd,len(object_pos_list)):
                    object_pos_list[i][12] = val
                    print object_pos_list[i]
            else:
                for i in range(0,len(object_pos_list)):       #Write to all
                    object_pos_list[i][12] = val
                    print object_pos_list[i]  

    def set_object14_pos(self,instance,val):
        global metadataInd, object_pos_list, record, write_mode
        if record == 1:
            if write_mode == 1:                                 #Write to end
                for i in range(metadataInd,len(object_pos_list)):
                    object_pos_list[i][13] = val
                    print object_pos_list[i]
            else:
                for i in range(0,len(object_pos_list)):       #Write to all
                    object_pos_list[i][13] = val
                    print object_pos_list[i] 

    def set_object15_pos(self,instance,val):
        global metadataInd, object_pos_list, record, write_mode
        if record == 1:
            if write_mode == 1:                                 #Write to end
                for i in range(metadataInd,len(object_pos_list)):
                    object_pos_list[i][14] = val
                    print object_pos_list[i]
            else:
                for i in range(0,len(object_pos_list)):       #Write to all
                    object_pos_list[i][14] = val
                    print object_pos_list[i] 

    def set_object16_pos(self,instance,val):
        global metadataInd, object_pos_list, record, write_mode
        if record == 1:
            if write_mode == 1:                                 #Write to end
                for i in range(metadataInd,len(object_pos_list)):
                    object_pos_list[i][15] = val
                    print object_pos_list[i]
            else:
                for i in range(0,len(object_pos_list)):       #Write to all
                    object_pos_list[i][15] = val
                    print object_pos_list[i]     
    
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
            self.btn_toggle_renderer.text = "Reference"
        else:
            rendererFlag = 1
            renderer_thread = threading.Thread(target=start_renderer,args=[1])
            renderer_thread.start()
            self.btn_toggle_renderer.text = "downmix"


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

    def switch_record_mode(self,instance,val):
        global write_mode
       
        if val == 'normal':          
            write_mode = 0
            self.btn_toggle_record_mode.text = "Write to all"
            
        else:
            write_mode = 1
            print write_mode
            self.btn_toggle_record_mode.text = "Write to end"


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
        global object_level, object_pos, folder_name, file_name, object_level_list, object_pos_list
        with open('./' + folder_name + '/' + str(file_name) + '.txt',"a") as myfile:
            myfile.write(str(object_level_list) + '\n')
            myfile.write(str(object_pos_list) + '\n')
        file_name = file_name + 1

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