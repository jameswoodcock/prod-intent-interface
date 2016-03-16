#Receive JSON object messages
import json
import socket
import sys
import time
import threading
import subprocess
import math
#from Tkinter import *

HOST = 'localhost'
PORT_R = 4242
PORT_S = 4240

#Global variables
objectIDs = [0,1,2,3,10,32,33,34,35,36]           #Number of objects
object_level = [1,1,1,1,1,1,1,1,1,1]
object_pos = [0,0,0,0,0,0,0,0,0,0,0]

renderer = 0

high_priority_val = 1

rendererFlag = 1

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

    #talk with client
    while 1:
        #receive data from client
        d = s.recvfrom(16384)
        data = d[0]
        addr = d[1]

        newmsg = json.loads(data.strip())

        if rendererFlag == 1:                       #Only operate on objects if downmix
            for j in range(len(objectIDs)):         #Cycle through object list
                #print 'j = ' + str(j)
                print rendererFlag
                newmsg['objects'][objectIDs[j]]['level'] = object_level[j]
                if newmsg['objects'][objectIDs[j]]['type'] == 'plane':
                    newmsg['objects'][objectIDs[j]]['direction']['az'] = object_pos[j]
                else:
                    newmsg['objects'][objectIDs[j]]['position']['x'] = math.cos(deg2rad(object_pos[j]))
                    newmsg['objects'][objectIDs[j]]['position']['y'] = math.sin(deg2rad(object_pos[j]))      
                #if newmsg['objects'][i]['priority'] == 1:
                    #print 'in if object' + str(i)
                    #newmsg['objects'][i]['level'] = high_priority_val

        newjsonmsg = json.dumps(newmsg)

        s.sendto(newjsonmsg,(HOST,PORT_S))

renderer_thread = threading.Thread(target=start_renderer,args=[renderer])
if renderer_thread.isAlive():
    print 'Its alive'
renderer_thread.start()


thread = threading.Thread(target=send_receive_json,args=(HOST,PORT_R,PORT_S))
thread.start()

#make GUI
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.slider import Slider
from kivy.uix.label import Label
from kivy.uix.togglebutton import ToggleButton

class mySlider(GridLayout):

    def __init__(self, **kwargs):
        super(mySlider, self).__init__(**kwargs)
        self.cols = 11
        object1_lev_slider = Slider(min=0, max=1,orientation='vertical')
        object1_pos_slider = Slider(min=-180, max=180,orientation='vertical')
        object2_lev_slider = Slider(min=0, max=1,orientation='vertical')
        object2_pos_slider = Slider(min=-180, max=180,orientation='vertical')
        object3_lev_slider = Slider(min=0, max=1,orientation='vertical')
        object3_pos_slider = Slider(min=-180, max=180,orientation='vertical')
        object4_lev_slider = Slider(min=0, max=1,orientation='vertical')
        object4_pos_slider = Slider(min=-180, max=180,orientation='vertical')
        object5_lev_slider = Slider(min=0, max=1,orientation='vertical')
        object5_pos_slider = Slider(min=-180, max=180,orientation='vertical')
        object6_lev_slider = Slider(min=0, max=1,orientation='vertical')
        object6_pos_slider = Slider(min=-180, max=180,orientation='vertical')
        object7_lev_slider = Slider(min=0, max=1,orientation='vertical')
        object7_pos_slider = Slider(min=-180, max=180,orientation='vertical')
        object8_lev_slider = Slider(min=0, max=1,orientation='vertical')
        object8_pos_slider = Slider(min=-180, max=180,orientation='vertical')
        object9_lev_slider = Slider(min=0, max=1,orientation='vertical')
        object9_pos_slider = Slider(min=-180, max=180,orientation='vertical')
        object10_lev_slider = Slider(min=0, max=1,orientation='vertical')
        object10_pos_slider = Slider(min=-180, max=180,orientation='vertical')
        btn_toggle_renderer = ToggleButton(text = "Switch renderer")     
        object1_lev_slider.bind(value=self.set_object1_level)
        object1_pos_slider.bind(value=self.set_object1_pos)
        object2_lev_slider.bind(value=self.set_object2_level)
        object2_pos_slider.bind(value=self.set_object2_pos)
        object3_lev_slider.bind(value=self.set_object3_level)
        object3_pos_slider.bind(value=self.set_object3_pos)
        object4_lev_slider.bind(value=self.set_object4_level)
        object4_pos_slider.bind(value=self.set_object4_pos)
        object5_lev_slider.bind(value=self.set_object5_level)
        object5_pos_slider.bind(value=self.set_object5_pos)
        object6_lev_slider.bind(value=self.set_object6_level)
        object6_pos_slider.bind(value=self.set_object6_pos)
        object7_lev_slider.bind(value=self.set_object7_level)
        object7_pos_slider.bind(value=self.set_object7_pos)
        object8_lev_slider.bind(value=self.set_object8_level)
        object8_pos_slider.bind(value=self.set_object8_pos)
        object9_lev_slider.bind(value=self.set_object9_level)
        object9_pos_slider.bind(value=self.set_object9_pos)
        object10_lev_slider.bind(value=self.set_object10_level)
        object10_pos_slider.bind(value=self.set_object10_pos)
        btn_toggle_renderer.bind(state=self.switch_renderer)
        self.add_widget(object1_lev_slider)        
        self.add_widget(object2_lev_slider)
        self.add_widget(object3_lev_slider)
        self.add_widget(object4_lev_slider)
        self.add_widget(object5_lev_slider)
        self.add_widget(object6_lev_slider)
        self.add_widget(object7_lev_slider)
        self.add_widget(object8_lev_slider)
        self.add_widget(object9_lev_slider)
        self.add_widget(object10_lev_slider)
        self.add_widget(btn_toggle_renderer)
        self.add_widget(object1_pos_slider)
        self.add_widget(object2_pos_slider)
        self.add_widget(object3_pos_slider)
        self.add_widget(object4_pos_slider)
        self.add_widget(object5_pos_slider)
        self.add_widget(object6_pos_slider)
        self.add_widget(object7_pos_slider)
        self.add_widget(object8_pos_slider)
        self.add_widget(object9_pos_slider)
        self.add_widget(object10_pos_slider)
        #self.add_widget(Label(text='Narrator level'))
        #self.add_widget(Label(text='Narrator position'))
        #self.add_widget(Label(text='Something else'))
        #self.add_widget(Label(text='Something else'))

    def set_object1_level(self,instance,val):
        global object_level
        object_level[0] = val
        print 'Obj1 level set to ' + str(object_level[0])

    def set_object2_level(self,instance,val):
        global object_level
        object_level[1] = val
        print 'Obj2 level set to ' + str(object_level[1])

    def set_object3_level(self,instance,val):
        global object_level
        object_level[2] = val
        print 'Obj3 level set to ' + str(object_level[2])

    def set_object4_level(self,instance,val):
        global object_level
        object_level[3] = val
        print 'Obj4 level set to ' + str(object_level[3])        

    def set_object5_level(self,instance,val):
        global narrator_level
        object_level[4] = val
        print 'Obj5 position set to ' + str(object_level[4])

    def set_object6_level(self,instance,val):
        global object_level
        object_level[5] = val
        print 'Obj6 level set to ' + str(object_level[5])

    def set_object7_level(self,instance,val):
        global object_level
        object_level[6] = val
        print 'Obj7 level set to ' + str(object_level[6])

    def set_object8_level(self,instance,val):
        global object_level
        object_level[7] = val
        print 'Obj8 level set to ' + str(object_level[7])

    def set_object9_level(self,instance,val):
        global object_level
        object_level[8] = val
        print 'Obj4 level set to ' + str(object_level[8]) 

    def set_object10_level(self,instance,val):
        global object_level
        object_level[9] = val
        print 'Obj10 level set to ' + str(object_level[9])    

    def set_object1_pos(self,instance,val):
        global object_pos
        object_pos[0] = val
        print 'Obj1 pos set to ' + str(object_pos[0])

    def set_object2_pos(self,instance,val):
        global object_pos
        object_pos[1] = val
        print 'Obj2 pos set to ' + str(object_pos[1])

    def set_object3_pos(self,instance,val):
        global object_pos
        object_pos[2] = val
        print 'Obj3 pos set to ' + str(object_pos[2])

    def set_object4_pos(self,instance,val):
        global object_pos
        object_pos[3] = val
        print 'Obj4 pos set to ' + str(object_pos[3])        

    def set_object5_pos(self,instance,val):
        global narrator_pos
        object_pos[4] = val
        print 'Obj5 position set to ' + str(object_pos[4])

    def set_object6_pos(self,instance,val):
        global object_pos
        object_pos[5] = val
        print 'Obj6 pos set to ' + str(object_pos[5])

    def set_object7_pos(self,instance,val):
        global object_pos
        object_pos[6] = val
        print 'Obj7 pos set to ' + str(object_pos[6])

    def set_object8_pos(self,instance,val):
        global object_pos
        object_pos[7] = val
        print 'Obj8 pos set to ' + str(object_pos[7])

    def set_object9_pos(self,instance,val):
        global object_pos
        object_pos[8] = val
        print 'Obj4 pos set to ' + str(object_pos[8]) 

    def set_object10_pos(self,instance,val):
        global object_pos
        object_pos[9] = val
        print 'Obj10 pos set to ' + str(object_pos[9])             
      
    def set_high_priority_level(self,instance,val):
        global high_priority_val
        high_priority_val = val
        print 'High priority set to ' + str(high_priority_val)

    def switch_renderer(self,instance,val):
        global renderer_thread 
        global rendererFlag
        #if renderer_thread.isAlive():
        #    renderer_thread.stop()
        if val == 'down':
            print "button is down"
            rendererFlag = 0
            renderer_thread = threading.Thread(target=start_renderer,args=[0])
            renderer_thread.start()
        else:
            print "button is up"
            rendererFlag = 1
            renderer_thread = threading.Thread(target=start_renderer,args=[1])
            renderer_thread.start()    


class MyApp(App):
    slider_update = mySlider()
    def build(self):
        return mySlider()

if __name__ == '__main__':
    MyApp().run()