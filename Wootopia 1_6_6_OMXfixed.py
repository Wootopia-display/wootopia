# -*- coding: UTF-8 -*-
#!/usr/bin/env python3
# OMX PLAYER BUG FIXED !
# 24h tested OK

# Version 1.6.6.fixed

# Imports pour le slider
from __future__ import absolute_import, division, print_function, unicode_literals
try:
    import pi3d
except:
    print("IMPORT Pi3D ERROR!")
    pass
import os
import subprocess
import struct
import time
import random
import ast
import threading

# import pour le port série RS232
import serial

# Imports pour OMXplayer-wrapper
try:
    from omxplayer.player import OMXPlayer
except:
    print("IMPORT OMXPLAYER ERROR!")
    pass

#import pour envois vers IP video player
import socket

# Imports pour input events (télécommande IR)
try:
    import evdev, selectors
except:
    print("IMPORT MODULE EVDEV ERROR!")
    pass

# Imports pour parsing XML
import xml.etree.ElementTree as ET

# Imports pour GPIO
import RPi.GPIO as GPIO

# HTTP server:begin

from threading import Thread

from http.server import BaseHTTPRequestHandler, HTTPServer

class S(BaseHTTPRequestHandler):
    def _set_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        self._set_response()
        if self.path=='/':
          with open("remote.html","r") as f:
            self.wfile.write(f.read().encode('utf-8'))
        else:
            self.wfile.write("GET request for {}".format(self.path).encode('utf-8'))
            if self.path[1:] in Scenario["Evenements"]["http"]:
                TraiteEvenement(Scenario["Evenements"]["http"][self.path[1:]])

    def do_POST(self):
        content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
        post_data = self.rfile.read(content_length) # <--- Gets the data itself
        print("POST request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n",str(self.path), str(self.headers), post_data.decode('utf-8'))
        self._set_response()
        self.wfile.write("POST request for {}".format(self.path).encode('utf-8'))

    def log_message(self, format, *args):
        return

def run_http(server_class=HTTPServer, handler_class=S, port=8080):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()

class http_listener(Thread):
    def run(self):
        run_http()

http_listener().start()

# HTTP server: end

# ouverture port RS232
try:
    RS232=serial.Serial("/dev/ttyUSB0", baudrate = 9600, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=1)
    RS232_ok=True
except:
    print("RS232_1 NOT FOUND")
    RS232_ok=False
    pass
    
# reception port RS232
try:
    RS232_receive=serial.Serial("/dev/ttyUSB0", baudrate = 9600,parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE,bytesize=serial.EIGHTBITS, timeout=1)
    if (RS232_receive):
        RS232_receive_ok=True
except:
    RS232_receive_ok=False
    pass

# ouverture port RS232_2
try:
    RS232_2=serial.Serial("/dev/ttyUSB1", baudrate = 9600, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=1)
    RS232_2_ok=True
except:
    print("RS232_2 NOT FOUND")
    RS232_2_ok=False
    pass
    
# reception port RS232_2
try:
    RS232_2_receive=serial.Serial("/dev/ttyUSB1", baudrate = 9600,parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE,bytesize=serial.EIGHTBITS, timeout=1)
    if (RS232_2_receive):
        RS232_2_receive_ok=True
except:
    RS232_2_receive_ok=False
    pass
    
Medias_path='medias'

GPIO.setmode(GPIO.BCM)
# numéros LED et GPIOs DMX - voir https://pinout.xyz/
# GPIO4 dispo sur CI V3 HAT
gpio_in4=4
# GPIO21 correspond a PCM DOUT pin40 dispo sur CI V3 HAT
led21=21
led22=22
# Attribution des PINS DMX - ne pas modifier ces valeurs
# GPIO 10 et 11 reserve Bus LED RVB
dmx0=26
dmx1=13
dmx2=16
dmx3=12
dmx4=6
dmx5=24
dmx6=23
GPIO.setup(gpio_in4, GPIO.IN)
#GPIO.setup(led21, GPIO.OUT)
#GPIO.setup(led22, GPIO.OUT)
GPIO.setup([dmx0,dmx1,dmx2,dmx3,dmx4,dmx5,dmx6], GPIO.OUT)

# Video input
PI3D_window_name="PI3Dwootopia"
VideoInput_window_name="ffplaywootopia"
VideoInputCommand="ffplay /dev/video0 -loop 0 -noborder -an -left 0 -top 0 -x 1280 -y 1024 -loglevel quiet -window_title " + VideoInput_window_name

# Imports pour skywriter
try :
    import skywriter
except:
    print('Avertissement : PAD non detecte')
    pass

Debug=False

azerty_hid_codes = {
  'a' : (0, 20), 'b' : (0, 5), 'c' : (0, 6), 'd' : (0, 7), 'e' : (0, 8), 'f' : (0, 9),
  'g' : (0, 10), 'h' : (0, 11), 'i' : (0, 12), 'j' : (0, 13), 'k' : (0, 14), 'l' : (0, 15),
  'm' : (0, 51), 'n' : (0, 17), 'o' : (0, 18), 'p' : (0, 19), 'q' : (0, 4), 'r' : (0, 21),
  's' : (0, 22), 't' : (0, 23), 'u' : (0, 24), 'v' : (0, 25), 'w' : (0, 29), 'x' : (0, 27),
  'y' : (0, 28), 'z' : (0, 26), '1' : (2, 30), '2' : (2, 31), '3' : (2, 32), '4' : (2, 33),
  '5' : (2, 34), '6' : (2, 35), '7' : (2, 36), '8' : (2, 37), '9' : (2, 38), '0' : (2, 39),
  'enter': (0, 40), '\b': (0, 42), 'escape': (0, 43), ' ' : (0, 44), '-' : (0, 35), '=' : (0, 46),
  '[' : (64, 34), ']' : (64, 45), '\\': (64, 37), ';' : (0, 54), '\'': (64, 33), '`' : (64, 36),
  ',' : (0, 16), ':' : (0, 55), '/' : (2, 55), 'A' : (2, 20), 'B' : (2, 5), 'C' : (2, 6),
  'D' : (2, 7), 'E' : (2, 8), 'F' : (2, 9), 'G' : (2, 10), 'H' : (2, 11), 'I' : (2, 12),
  'J' : (2, 13), 'K' : (2, 14), 'L' : (2, 15), 'M' : (2, 51), 'N' : (2, 17), 'O' : (2, 18),
  'P' : (2, 19), 'Q' : (2, 4), 'R' : (2, 21), 'S' : (2, 22), 'T' : (2, 23), 'U' : (2, 24),
  'V' : (2, 25), 'W' : (2, 29), 'X' : (2, 27), 'Y' : (2, 28), 'Z' : (2, 26), '!' : (0, 56),
  '@' : (64, 39), '#' : (64, 32), '$' : (0, 48), '%' : (32, 52), '^' : (64, 38), '&' : (0, 30),
  '*' : (0, 49), '(' : (0, 34), ')' : (0, 45), '_' : (0, 37), '+' : (2, 46), '{' : (64, 33),
  '}' : (64, 46), '|' : (64, 35), '.' : (2, 54), '"' : (0, 32), '~' : (64, 31), '<' : (0, 100),
  '>' : (2, 100), '?' : (2, 16), 'Haut' : (0, 96), 'Bas' : (0, 90), 'Gauche' : (0, 92), 'Droite' : (0, 94)}


# Préparation input events (télécommande IR)
selector = selectors.DefaultSelector()

devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
for device in devices:
   if device.name=="HID 1d57:ad02 Consumer Control": IRconsumer = evdev.InputDevice(device.path)
   if device.name=="HID 1d57:ad02 Keyboard": IRkeyboard = evdev.InputDevice(device.path)

try:
   IRconsumer.grab() # accès exclusif au device (important pour éviter intéractions avec le système)
   IRkeyboard.grab() # accès exclusif au device

   selector.register(IRconsumer, selectors.EVENT_READ)
   selector.register(IRkeyboard, selectors.EVENT_READ)
except:
   pass

# variables globales du slider qui ne changent pas une fois initialisées
RepertoireMediaIni='/home/pi/Documents/Slider/medias.ini'
AllMedias = []          # liste de tous les objets Medias
categories=[]           # Liste des noms de catégories
sous_categories=[]      # Liste de listes de sous-catégories

# variables globales du slider qui dépendent du contexe, c'est à dire de la catégorie et de la sous catégorie sélectionnées
Medias=[]               # Liste des médias de la catégorie (et éventuellement sous-catégorie) courante 
NextMedias=[]           # Liste des médias qui vont remplacer les anciens médias 
cats=[]                 # Liste des textes pi3d des catégories
souscats=[]             # Liste des textes pi3d des sous-catégories
cats2=[]                # Pour l'affichage en haut à gauche : Liste des textes pi3d des catégories
souscats2=[]            # Pour l'affichage en haut à gauche : Liste des textes pi3d des sous-catégories

slider_mode='selection' # mode a 3 valeurs possibles : selection / categorie / souscategorie
slider_visible=False
slider_stop=False

PAD_z=1.0
PAD_Actif=False
PAD_Timeout=-1
PAD_Timeout_Delay=200 # 2 secondes avant que le PAD soit considéré inactif
PAD_Transition_duree=10
PAD_Transition=-PAD_Transition_duree # activation de -PAD_Transition_duree à 0, désactivation de +PAD_Transition_duree à 0
PAD_seuil_detection=0.99

Slider_previously_selected_media=0
current_media=0
next_current_media=0
current_cat=0
current_souscat=-1

slider_action=''
move_steps=0            # à quelle étape en est la transition - technique utilisée pour le défilement des objets
nb_max_steps=10         # indique sur combien de frames s'effectue la transition
move_steps_media=0      # à quelle étape en est la transition des médias
move_steps_cat=0        # à quelle étape en est la transition des catégories
move_steps_souscat=0

# ********** Fonctions

Player=None
PlayedMediaId=None
MediaAssociations={}
MediaTimeline={}
IRremotePrevious=0
Sub=[]

def playerExit(exit_code):
    if Player._connection._bus is not None:
        Player._connection._bus.close()
    global PlayedMediaId, PlaylistNext, MediaTimeline
    mediaid=PlayedMediaId
    PlayedMediaId=None
    MediaAssociations={}
    MediaTimeline={}
    if PlaylistNext:
      if Scenario["Medias"][mediaid]["mediasuivant"]=="random":
          PlayMedia(random.choice(list(Scenario["Medias"])))
      elif Scenario["Medias"][mediaid]["mediasuivant"]:
          PlayMedia(Scenario["Medias"][mediaid]["mediasuivant"])

def PlayMedia(mediaid):
    global Player, PlayedMediaId, MediaAssociations, MediaTimeline, Sub, PlaylistNext
    PlayedMediaId=mediaid
    PlaylistNext=True
    if mediaid in Scenario["Medias"]:
        MediaAssociations=Scenario["Medias"][mediaid]["associations"]
        MediaTimeline=Scenario["Medias"][mediaid]["timeline"].copy()
        # print(mediaid)
        # print(MediaTimeline)
        Mediafile = Medias_path + '/' + Scenario["Medias"][mediaid]["filename"]
        if (os.path.isfile(Mediafile)):
            Player=OMXPlayer(Mediafile,args=Scenario["Medias"][mediaid]["arguments"].split(' '))
            # print(Scenario["Medias"][mediaid]["arguments"])
            if Scenario["Medias"][mediaid]["positionecran"] is not None:
                pos=Scenario["Medias"][mediaid]["positionecran"].split(',')
                Player.set_video_pos(int(pos[0]),int(pos[1]),int(pos[2]),int(pos[3]))
            else:
                TerminateProcesses(Sub,None)
            Player.exitEvent += lambda _, exit_code: playerExit(exit_code)

def TerminateProcesses(ProcessList,nom):
    for p in ProcessList:
        if nom==None or nom==p["nom"]:
            if p["process"].poll()==None:
                p["process"].stdin.write(ast.literal_eval("b'"+p["terminate"]+"'"))
                p["process"].stdin.flush()


def Lance(actionid):
    if Debug: print("*** actionid *** ",actionid)
    global Player, PlayedMediaId, Sub, slider_visible, slider_mode, slider_stop, slider_timeout, Slider_previously_selected_media
    global Medias, current_media, PlaylistNext, VideoInputProcess
    global RS232, RS232_ok, RS232_2, RS232_2_ok
    if actionid in Scenario["Actions"]:
        Programme=Scenario["Actions"][actionid]["programme"]
        Commande=Scenario["Actions"][actionid]["commande"]
        if Programme=="Slider":
            slider_timeout=SLIDER_TIMEOUT
            if Commande=="SliderStart":
                slider_visible=True
            elif Commande=="SliderStop":
                if Debug: print('slider_stop=True')
                slider_stop=True
            elif Commande=="SliderOnOff":
                slider_visible = not slider_visible
            elif Commande=="SliderActionSelection":
                slider_visible = False
                if Slider_previously_selected_media != current_media:
                  Lance(Medias[current_media].action)                
                Slider_previously_selected_media=current_media
            elif Commande=="SliderLeft":
                if slider_mode=="selection":
                    SliderGaucheSelection()
                elif slider_mode=="categorie": 
                    SliderAfficherSelection()
                elif slider_mode=="souscategorie":
                    SliderAfficherCategories()
            elif Commande=="SliderRight":
                if slider_mode=="selection":
                    SliderDroiteSelection()
                elif slider_mode=='categorie' and (len(sous_categories[current_cat]) > 1): # la catégorie contient plusieurs sous catégories
                    SliderAfficherSousCategories()
                elif slider_mode=='categorie' and (len(sous_categories[current_cat]) <= 1): # la catégorie contient 0 ou 1 seule sous catégorie
                    SliderAfficherSelection()
                elif slider_mode=='souscategorie':
                    SliderAfficherSelection()
            elif Commande=="SliderUp":
                if slider_mode=="selection":
                    SliderAfficherCategories()
                elif slider_mode=="categorie":
                    SliderHautCategories()
                elif slider_mode=="souscategorie":
                    SliderHautSousCategories()
            elif Commande=="SliderDown":
                if slider_mode=="categorie":
                    SliderBasCategories()
                elif slider_mode=="souscategorie":
                    SliderBasSousCategories()
            elif Commande=="SliderAfficherMedias":
                slider_visible=True
                SliderAfficherSelection()
            elif Commande=="SliderAfficherCategories":
                SliderAfficherCategories()
            elif Commande=="SliderAfficherSousCategories":
                SliderAfficherSousCategories()
            elif Commande=="SliderDump": # Utilisé pour le débogage
                SliderDump()
        elif Programme=="PlayMedia":
            PlayMedia(Commande)
        elif Programme=="MediaControl":
            if PlayedMediaId:
                try:
                    if Commande=="Pause": Player.pause()
                    if Commande=="Desactive":
                      Player.hide_video()
                      Player.pause()
                    if Commande=="Active":
                      Player.play()
                      Player.show_video()
                    if Commande=="Resume": Player.play()
                    if Commande=="Stop": Player.quit()
                    if Commande=="StopAll":
                      PlaylistNext=False
                      Player.quit()
                except:
                    pass
        elif Programme=="LED21":
            if Commande=="on": GPIO.output(led21, 1)
            if Commande=="off": GPIO.output(led21, 0)
        elif Programme=="LED22":
            if Commande=="on": GPIO.output(led22, 1)
            if Commande=="off": GPIO.output(led22, 0)
        elif Programme[0:10]=="Subprocess":
            Sub.append({'process':subprocess.Popen(Commande.split(' '), shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE),
                        'nom':Programme.split('|')[1],
                        'terminate':Programme.split('|')[2]})
        elif Programme=="StopSubprocess":
            TerminateProcesses(Sub,Commande)
        elif Programme[0:13]=="IPvideoPlayer":
            try:
                IPvideoplayerSocket=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                IPvideoplayerSocket.connect((Programme.split('|')[1], int(Programme.split('|')[2])))  # Programme="IPvideoPlayer|TCP_IP|TCP_PORT"
                #IPvideoplayerSocket.send(bytes(Commande.encode()))
                IPvideoplayerSocket.send(eval('b"'+Commande+'"'))
                IPvideoplayerSocket.close()
                print("IP video Player IP:" + Programme.split('|')[1] + " port:" + Programme.split('|')[2] + " commande: " + Commande)
            except:
                print("IP video Player IP not connected!")
                pass
        elif Programme=="Clavier":
            wantedChar=Commande
            modif, key = azerty_hid_codes[wantedChar]
            raw = struct.pack("BBBBL", modif, 0x00, key, 0x00, 0x00000000)
            with open("/dev/hidg0", "wb") as f:
                f.write(raw) # press key
                f.write(struct.pack("Q", 0)) # release key
        elif Programme=="CommandeDMX":
            pins=list(str(bin(int(Commande)))[2:].zfill(7))
            pins.reverse()
            GPIO.output([dmx0,dmx1,dmx2,dmx3,dmx4,dmx5,dmx6],(int(pins[0]),int(pins[1]),int(pins[2]),int(pins[3]),int(pins[4]),int(pins[5]),int(pins[6])))
        elif Programme=="Video_input":
            if Commande=="Start":
                # VideoInputProcess = subprocess.Popen(VideoInputCommand.split(' '),stdin=subprocess.PIPE,stdout=None,stderr=None,bufsize=0)
                Sub.append({'process':subprocess.Popen(VideoInputCommand.split(' '), shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE),
                            'nom':'VideoInputProcess',
                            'terminate':"\033"})
                os.system("sleep 5 && xdotool search --name " + PI3D_window_name + " windowraise")
            elif Commande=="Stop":
                # TerminateProcesses(Sub,'VideoInputProcess')
                # VideoInputProcess.terminate()
                os.system("xdotool search --name " + VideoInput_window_name + " key q")
        elif Programme=="RS232":
            if RS232_ok:
                for commande_unitaire in Commande.split("|"):
                    RS232.write(bytes(commande_unitaire.encode()))
                    time.sleep(0.1)
            else:
                print('RS232 non disponible - commande ' + Commande + ' non transmise')
        elif Programme=="RS232_2":
            if RS232_2_ok:
                for commande_unitaire in Commande.split("|"):
                    RS232_2.write(bytes(commande_unitaire.encode()))
                    time.sleep(0.1)
            else:
                print('RS232_2 non disponible - commande ' + Commande + ' non transmise')
        
        elif Programme=="Shutdown":
            slider_stop=True
            GPIO.cleanup()
            if RS232_ok:
                RS232.close()
            if RS232_2_ok:
                RS232_2.close()
            if Commande=="reboot":
                os.system("reboot")
            else:
                os.system("shutdown now")
        else:
            if Debug: print(Scenario["Actions"][actionid])
    else:
        raise LookupError(actionid + " n'est pas une action connue")

def TraiteEvenement(eventid):
    global MediaAssociations
    if eventid in Scenario["Associations"]:
        for actionid in Scenario["Associations"][eventid]:
            Lance(actionid)
    if eventid in MediaAssociations:
        for actionid in MediaAssociations[eventid]:
            Lance(actionid)

def telecommande_read(): # Telecommande Infrarouge
    global IRremotePrevious
    while not slider_stop:
      for key, mask in selector.select():
          device = key.fileobj
          for event in device.read():
              if Debug: print('event.type = ',event.type)
              if event.type == 4:
                  if event.value == IRremotePrevious:
                      IRremotePrevious=0
                  else:
                      eventid=str(event.value)
                      print("Telecommande: "+eventid)
                      if eventid in Scenario["Evenements"]["Remote"]:
                          TraiteEvenement(Scenario["Evenements"]["Remote"][eventid])
                      else:
                          if Debug: print(eventid)
                      IRremotePrevious=event.value
    

SLIDER_TIMEOUT = 10000


# ********** Charge le fichier XML du scenario dans un dictionnaire

tree=ET.parse('Wootopia.xml')
root=tree.getroot()

Scenario={"Evenements":{},"Actions":{},"Associations":{},"Medias":{}}
for action in root.find("actions"):
    Scenario["Actions"][action.attrib['actionid']]={
        "programme":action.find('programme').text,
        "commande":action.find('commande').text
    }
for evenement in root.find("evenements"):
    source=evenement.find('source').text
    if (source=='Slider') and (evenement.attrib['evenementid']=='Slider_Timeout'): SLIDER_TIMEOUT=int(evenement.find('valeur').text)
    if not source in Scenario["Evenements"]: Scenario["Evenements"][source]={}
    Scenario["Evenements"][source][evenement.find('valeur').text]=evenement.attrib['evenementid']
for association in root.find("associations"):
    if not association.find('evenement').text in Scenario["Associations"]:
        Scenario["Associations"][association.find('evenement').text]=[]
    Scenario["Associations"][association.find('evenement').text].append(association.find('action').text)
for media in root.find("medias"):
    mediaid=media.attrib['mediaid']
    Scenario["Medias"][mediaid]={
        "filename":media.find('filename').text,
        "positionecran":media.find('positionecran').text,
        "arguments":media.find('arguments').text,
        "mediasuivant":media.find('mediasuivant').text,
        "associations":{},
        "timeline":{}
    }
    for association in media.find("associations"):
        if not association.find('evenement').text in Scenario["Medias"][mediaid]["associations"]:
            Scenario["Medias"][mediaid]["associations"][association.find('evenement').text]=[]
        Scenario["Medias"][mediaid]["associations"][association.find('evenement').text].append(association.find('action').text)
    for event in media.find("timeline"):
        if not event.find('seconds10').text in Scenario["Medias"][mediaid]["timeline"]:
            Scenario["Medias"][mediaid]["timeline"][event.find('seconds10').text]=[]
        Scenario["Medias"][mediaid]["timeline"][event.find('seconds10').text].append(event.find('action').text)

# ********** RS232 receive

def RS232receiveThread():
    if RS232_receive_ok and "RS232_receive" in Scenario["Evenements"]:
        while RS232_receive:
            RS232_line=RS232_receive.readline()
            if RS232_line:
                for RS232_receive_expected in Scenario["Evenements"]["RS232_receive"]:
                    if eval(RS232_receive_expected) == RS232_line:
                        print("Reception RS232 correspondant à l'événement " + RS232_receive_expected)
                        TraiteEvenement(Scenario["Evenements"]["RS232_receive"][RS232_receive_expected])
                    else:
                        print("Reception RS232 " + RS232_receive_expected + " (aucun événement ne correspond)")

#threading.Thread(target=RS232receiveThread).start()

class RS232_listener(Thread):
    def run(self):
        RS232receiveThread()

RS232_listener().start()

# ********** RS232_2 receive

def RS232_2receiveThread():
    if RS232_2_receive_ok and "RS232_2_receive" in Scenario["Evenements"]:
        while RS232_2_receive:
            RS232_line=RS232_2_receive.readline()
            if RS232_2_line:
                for RS232_2_receive_expected in Scenario["Evenements"]["RS232_2_receive"]:
                    if eval(RS232_2_receive_expected) == RS232_2_line:
                        print("Reception RS232_2 correspondant à l'événement " + RS232_2_receive_expected)
                        TraiteEvenement(Scenario["Evenements"]["RS232_2_receive"][RS232_2_receive_expected])
                    else:
                        print("Reception RS232_2 " + RS232_2_receive_expected + " (aucun événement ne correspond)")

#threading.Thread(target=RS232receiveThread).start()

class RS232_2_listener(Thread):
    def run(self):
        RS232_2receiveThread()

RS232_2_listener().start()

# ********** GPIO

def GPIO_DOWN(channel):
  if (channel==4):
    TraiteEvenement(Scenario["Evenements"]["GPIO_DOWN"]["4"])

if "GPIO_DOWN" in Scenario["Evenements"]:
    if "4" in Scenario["Evenements"]["GPIO_DOWN"]:
        GPIO.add_event_detect(4, GPIO.FALLING, callback=GPIO_DOWN)  # FALLING or RISING

# ********** Slider timeout
slider_timeout = SLIDER_TIMEOUT 

def SliderTimeout():
  global slider_timeout, Medias, current_media
  slider_timeout=SLIDER_TIMEOUT
      #TraiteEvenement('Slider_Timeout')
  # slider_visible=False
  # Lance(Medias[current_media].action)
  

# Telecommande
class Telecommande(Thread):
    def run(self):
        telecommande_read()

Telecommande().start()

# Skywriter

try:
    
  @skywriter.flick()
  def flick(start,finish):
    if start+"-"+finish in Scenario["Evenements"]["PAD"]:
      TraiteEvenement(Scenario["Evenements"]["PAD"][start+"-"+finish])
    # if Debug: print('Got a flick!', start, finish)
    """ 
  @skywriter.airwheel()
  def airwheel(delta):
    if delta>0:
      TraiteEvenement(Scenario["Evenements"]["PAD"]["airwheel-horaire"])
      time.sleep(1)
      delta=0
    if delta<0:
      TraiteEvenement(Scenario["Evenements"]["PAD"]["airwheel-antihoraire"])
      time.sleep(1)
      delta=0
    print('Airwheel',delta)
    """      
  @skywriter.move()
  def move(xp, yp, zp):
    global PAD_z
    PAD_z=zp
    pass

except:
    pass


# ********** Paramètres d'affichage du slider - gestionaire de transparence dans le fenetrage

subprocess.Popen('xcompmgr', shell=False)

BACKGROUND = (0, 0, 0, 0)
#DISPLAY = pi3d.Display.create(background=BACKGROUND, frames_per_second=10, display_config=pi3d.DISPLAY_CONFIG_FULLSCREEN)
DISPLAY = pi3d.Display.create(background=BACKGROUND, frames_per_second=40, w=400, h=400, use_glx=True, window_title="Wootopia")
# DISPLAY = pi3d.Display.create(background=BACKGROUND, frames_per_second=40, w=100, h=100, use_glx=True)
# DISPLAY = pi3d.Display.create(background=BACKGROUND, frames_per_second=40, display_config=pi3d.DISPLAY_CONFIG_FULLSCREEN, use_glx=True, layer=2, window_title=PI3D_window_name)
SHADER = pi3d.Shader("uv_flat")

Blur=True
Blur=False
Fog=True

if Blur:
  defocus = pi3d.Defocus()
mykeys = pi3d.Keyboard()
action = ''




#taille=10

distance_mediax = 20 # distance horizontale entre les images
distance_mediay = 10 # distance verticale entre les images en cours et les prochaines images
distance_mediaz = 20 # distance verticale entre l'image sélectionnée et les autres images
recul=40 # recul de la caméra
#recul=80

distance=20 # coefficient général pour l'affichage des catégories
distance_caty=0.7
distance_catz=0.08
nb_step_cat=10 # nombre de steps pour passer d'une catégorie à une autre
nb_step_souscat=10 # nombre de steps pour passer d'une sous catégorie à une autre
nb_step_media=10 # nombre de steps pour paser d'un média à un autre - déplacement horizontal
nb_step_groupe_media=10 # nombre de steps pour paser d'un groupe de médias à un autre - déplacement vertical

PlaylistNext=True  # détermine si la playlist doit passer au média suivant ou s'arrêter 

CAMERA=pi3d.Camera.instance()
CAMERA.position((0,0,-recul))

"""
hand = pi3d.Model(file_string='hand.obj', name='hand') # image de la main
hand.set_shader(SHADER)
sprite = pi3d.ImageSprite("PAD.png", SHADER, w=10.0, h=6.0) # image de la tablette
"""

# ********** Initialisation des formes géométriques Fleche et Cadre

# Initialisation de la fleche
lfleche = 0.10 # largeur de la fleche
hfleche = 0.125 # hauteur de la fleche
fleche = pi3d.Lines(vertices=[[0, hfleche/4, 0],[2*lfleche/3, hfleche/4 , 0],[2*lfleche/3, hfleche/2, 0],[lfleche,0,0],[2*lfleche/3, -hfleche/2, 0],[2*lfleche/3, -hfleche/4, 0],[0, -hfleche/4, 0],[0, hfleche/4, 0]],x=0, y=0, z=0, material=(1.0,0.8,0.05),line_width=4)
fleche.position(0.27,0,-39)
fleche.shader = pi3d.Shader("mat_flat")

# Initialisation du cadre pour la catégorie en cours
lcadre = 0.5
hcadre = 0.125
cadre = pi3d.Lines(vertices=[[-lcadre/2, -hcadre/2, 0],[-lcadre/2, hcadre/2 , 0],[lcadre/2, hcadre/2, 0],[lcadre/2,-hcadre/2,0],[-lcadre/2, -hcadre/2, 0]],x=0, y=0, z=0, material=(1.0,0.8,0.05),line_width=4)
cadre.position(0,0,-39)
cadre.shader = pi3d.Shader("mat_flat")



# ********** Fonctions pour la gestion des medias, des categories et des sous categories

  
class CMedia:
  def __init__(self, chemin_image, chemin_vignette, desc, action, cats_souscats):
    # par exemple, cats_souscats = "Chaussures Hommes|Hiver;Chaussures Hommes|Sport"
    cats = []
    souscats = []
    elts = cats_souscats.split(";")
    for elt in elts:
      cats.append(elt.split("|")[0])
      souscats.append(elt.split("|")[1])
    self.cats = cats
    self.souscats = souscats
    self.desc = desc
    self.action = action
    self.media = pi3d.ImageSprite(chemin_image, shader=SHADER, w=13, h=9.3, x=0, y=0, z=0)
    self.mediadesc = pi3d.String(font=pi3d.Font("/home/pi/Documents/pi3d_demos/fonts/NotoSerif-Regular.ttf", (255, 255, 255, 255)), string=desc, x=0, y=0, z=0)
    self.mediadesc.set_shader(SHADER)
    #self.vignette = pi3d.ImageSprite(chemin_vignette, shader=SHADER, w=13, h=9.3, x=0, y=0, z=0)

def filtrerParCategorie(nom_cat):
  if Debug: print("filtrerParCategorie : ",nom_cat)
  res = []
  for cm in AllMedias:
    if nom_cat in cm.cats:
      res.append(cm)
  return res
  
def filtrerParSousCategorie(nom_cat, nom_souscat):
  if Debug: print("filtrerParSousCategorie : ",nom_cat," : ",nom_souscat)
  res = []
  for cm in AllMedias:
    i = 0
    trouve = False
    while (i < len(cm.cats)) and (trouve == False):
      if (nom_cat == cm.cats[i]) and (nom_souscat == cm.souscats[i]):
        trouve = True
        res.append(cm)
      else:
        i =i+1
  return res
  
# Chargement de la totalité des médias à partir du fichier media.ini

f = open(RepertoireMediaIni, "r")
for l in f:
  # si la ligne n'est pas vide et son première caractère est différent de [ et de #, alors traiter la ligne
  if (len(l) > 0) and (l[0]!='[') and (l[0]!='#'):
    if (l[-1]=='\n'):
      l = l[0:len(l)-1]
    t = l.split(';')
    catssouscats = ""
    i = 4 
    while i < len(t):
      if i == 4:
        catssouscats = t[i]
      else:
        catssouscats = catssouscats + ";" + t[i]
      cat = t[i].split("|")[0]
      souscat = t[i].split("|")[1]
      if not(cat in categories):
        categories.append(cat)
        sous_categories.append([])
      x = categories.index(cat)
      if not(souscat in sous_categories[x]):
        sous_categories[x].append(souscat)
      i = i+1
    AllMedias.append(CMedia(t[0],t[1],t[2], t[3], catssouscats))
    
if Debug: print(categories)
if Debug: print(sous_categories)

# ********** Fonctions de transition pour les medias vers le haut ou vers le bas

def transitionMediaBas(etape, maxetape):
  i=0
  for Media in Medias:
    x=(i-current_media)*distance_mediax
    y=-(etape/maxetape)*distance_mediay
    if i == current_media:
      z=-distance_mediaz
    else:
      z=0
    Media.media.position(x,y,z)
    i=i+1
    
  i=0
  for Media in NextMedias:
    x=(i-next_current_media)*distance_mediax
    y=distance_mediay*(1-etape/maxetape)
    if i == next_current_media:
      z=-distance_mediaz
    else:
      z=0
    Media.media.position(x,y,z)
    i=i+1
        
def transitionMediaHaut(etape, maxetape):
  i=0
  for Media in Medias:
    x=(i-current_media)*distance_mediax
    y=distance_mediay*(etape/maxetape)
    if i == current_media:
      z=-distance_mediaz
    else:
      z=0
    Media.media.position(x,y,z)
    i=i+1
    
  i=0
  for Media in NextMedias:
    x=(i-next_current_media)*distance_mediax
    y=distance_mediay*(etape/maxetape - 1)
    if i == next_current_media:
      z=-distance_mediaz
    else:
      z=0
    Media.media.position(x,y,z)
    i=i+1

# ********** Actions du slider

def SliderDump():
    if Debug: print("Début Slider dump")
    if Debug: print('slider_visible = ',slider_visible)
    if Debug: print('slider_mode = ',slider_mode)
    if Debug: print('current_media = ',current_media)
    if Debug: print('next_current_media = ',next_current_media)
    if Debug: print('current_cat = ',current_cat)
    if Debug: print('current_souscat = ',current_souscat)
    if Debug: print('len(Medias) = ',len(Medias))
    if Debug: print('Scenario["Associations"]["Slider_Timeout"] = ',Scenario["Associations"]["Slider_Timeout"])
    if Debug: print("Fin Slider dump")
    
def SliderInitialiserAffichage():
    global current_cat, current_souscat, cats, cats2, souscats2, Medias
    current_cat=0 # indice de la première catégorie à afficher
    current_souscat=-1 # indice de la sous-catégorie à afficher, -1 pour afficher toutes les sous-catégories

    #Initialiser les catégories et les sous catégories
    cats=[]
    cats2=[]
    souscats2=[]
    i=0
    for categorie in categories:
      x=0
      y=(i-current_cat)*distance_caty
      z=-distance*(1.8-(abs(i-current_cat)*distance_catz))
      a=pi3d.String(font=pi3d.Font("/home/pi/Documents/pi3d_demos/fonts/NotoSerif-Regular.ttf", (255, 255, 255, 255)), string=categorie, x=x, y=y, z=z)
      a.set_shader(SHADER)
      cats.append(a)
      cats2.append(a)
      res=[]
      for souscategorie in sous_categories[i]:
        a=pi3d.String(font=pi3d.Font("/home/pi/Documents/pi3d_demos/fonts/NotoSerif-Regular.ttf", (255, 255, 255, 255)), string=souscategorie, x=0, y=0, z=0)
        a.set_shader(SHADER)
        res.append(a)
      souscats2.append(res)
      i=i+1
    
    # Initialiser Medias
    if current_souscat == -1:
      Medias = filtrerParCategorie(categories[current_cat])
    else:
      Medias = filtrerParSousCategorie(categories[current_cat], sous_categories[current_cat][current_souscat])


def SliderAfficherSelection():
    global current_media, slider_mode
    slider_mode='selection'
    # Positionner les médias
    nb_images = len(Medias)
    if nb_images > 1:
      current_media=1 # on prend le deuxième média de la liste
    else:
      current_media=0 # on prend le média unique de la liste
      
    i=0
    for Media in Medias:
      x=(i-1)*distance_mediax
      y=0
      if i == current_media:
        z=-distance_mediaz
      else:
        z=0
      Media.media.position(x,y,z)
      i=i+1

def SliderDroiteSelection():
    global move_steps_media, slider_action
    if current_media < len(Medias)-1:
        # Important : l'instruction slider_action= doit être la dernière car c'est elle qui déclenche la transition visuelle    
        move_steps_media=1
        slider_action = 'DroiteSelection'

def SliderGaucheSelection():
    global move_steps_media, slider_action
    if current_media > 0:
        # Important : l'instruction slider_action= doit être la dernière car c'est elle qui déclenche la transition visuelle    
        move_steps_media=1
        slider_action = 'GaucheSelection'
 
def SliderAfficherCategories():
    global slider_mode, slider_action, NextMedias, move_steps, next_current_media
    if slider_mode!='categorie':
        if slider_mode=='souscategorie':
            slider_mode='categorie'
            cat = cats[current_cat]
            cat.position(0,0,-distance*1.8)
            NextMedias=filtrerParCategorie(categories[current_cat])
      
            if (len(NextMedias)>1):
                next_current_media=1
            else:
                next_current_media=0
            
            # Important : l'instruction slider_action= doit être la dernière car c'est elle qui déclenche la transition visuelle    
            move_steps=0
            slider_action="AfficherCategoriesAvecChangementMedia"
        else:
            slider_mode='categorie'
            cat = cats[current_cat]
            cat.position(0,0,-distance*1.8)
        
def SliderHautCategories():
    global slider_mode, slider_action, move_steps_cat, current_cat, next_cat, next_current_media, categories, NextMedias
    if (slider_mode=='categorie') and (current_cat < len(categories)-1):
        next_cat = current_cat+1
        NextMedias=filtrerParCategorie(categories[next_cat])
      
        if (len(NextMedias)>1):
            next_current_media=1
        else:
            next_current_media=0
         
        # Important : l'instruction slider_action= doit être la dernière car c'est elle qui déclenche la transition visuelle
        move_steps_cat=0
        slider_action = "HautCategories"

def SliderBasCategories():
    global slider_mode, slider_action, move_steps_cat, current_cat, next_cat, next_current_media, categories, NextMedias
    if (slider_mode=='categorie') and (current_cat > 0):
        next_cat = current_cat-1
        NextMedias=filtrerParCategorie(categories[next_cat])

        if (len(NextMedias)>1):
            next_current_media=1
        else:
            next_current_media=0
            
        # Important : l'instruction slider_action= doit être la dernière car c'est elle qui déclenche la transition visuelle
        move_steps_cat=0
        slider_action = 'BasCategories'
    
def SliderAfficherSousCategories():
    global slider_action, slider_mode, move_steps, current_cat, current_souscat, souscats, next_current_media, NextMedias
    if len(sous_categories[current_cat]) > 1:
        
        slider_mode='souscategorie'
        current_souscat = 1
      
        #Initialiser les sous catégories
        souscats=[]
        i=0
        for souscategorie in sous_categories[current_cat]:
            x=0
            y=(i-current_souscat)*distance_caty
            z=-distance*(1.8-(abs(i-current_souscat)*distance_catz))
            #z=-distance*1.8
            if Debug: print('pi3d.String : ',souscategorie)
            a=pi3d.String(font=pi3d.Font("/home/pi/Documents/pi3d_demos/fonts/NotoSerif-Regular.ttf", (255, 255, 255, 255)), string=souscategorie, x=x, y=y, z=z)
            a.set_shader(SHADER)
            souscats.append(a)
            i=i+1
        
        NextMedias = filtrerParSousCategorie(categories[current_cat], sous_categories[current_cat][current_souscat])
        if Debug: print('dans SliderAfficherSousCategories(), len(NextMedias) = ',len(NextMedias))
      
        if (len(NextMedias)>1):
          next_current_media=1
        else:
          next_current_media=0
          
        # Important : l'instruction slider_action= doit être la dernière car c'est elle qui déclenche la transition visuelle
        move_steps=0
        slider_action='AfficherSousCategories'
        
        
def SliderHautSousCategories():
    global slider_action, move_steps_souscat, next_souscat, NextMedias, next_current_media
    if (slider_mode=='souscategorie') and (current_souscat < len(sous_categories[current_cat])-1):
        next_souscat = current_souscat+1
        NextMedias=filtrerParSousCategorie(categories[current_cat], sous_categories[current_cat][next_souscat])

        if (len(NextMedias)>1):
            next_current_media=1
        else:
            next_current_media=0
        
        # Important : l'instruction slider_action= doit être la dernière car c'est elle qui déclenche la transition visuelle    
        move_steps_souscat=0
        slider_action='HautSousCategories'
    

          
def SliderBasSousCategories():
    global slider_action, move_steps_souscat, next_souscat, NextMedias, next_current_media
    if (slider_mode=='souscategorie') and (current_souscat > 0):
        next_souscat = current_souscat-1
        NextMedias=filtrerParSousCategorie(categories[current_cat], sous_categories[current_cat][next_souscat])

        if (len(NextMedias)>1):
          next_current_media=1
        else:
          next_current_media=0
          
        # Important : l'instruction slider_action= doit être la dernière car c'est elle qui déclenche la transition visuelle    
        move_steps_souscat=0  
        slider_action='BasSousCategories'
 


#Initialisation Slider
SliderInitialiserAffichage()
SliderAfficherSelection()

print("******************")
print("****** Prêt ******")
print("******************")

# DISPLAY.destroy()
# while False:
# boucle de gestion affichage 3D tant que pas detruit

while DISPLAY.loop_running():
  
  # ********** Lance la commande Start si elle existe
  if "Start" in Scenario["Associations"]:
      for actionid in Scenario["Associations"]["Start"]:
          Lance(actionid)
      Scenario["Associations"].pop("Start", None)

  
  if PAD_z < PAD_seuil_detection:
    PAD_Timeout=-1
  if (PAD_z < PAD_seuil_detection) and (not PAD_Actif):
    PAD_Actif=True
    PAD_Transition=-PAD_Transition_duree
    TraiteEvenement("PAD_Actif")
  if (PAD_z >= PAD_seuil_detection) and (PAD_Actif):
    if PAD_Timeout==-1:
      PAD_Timeout=round(time.time()*100)
      if Debug: print(PAD_Timeout)
    else:
      if Debug: print(round(time.time()*100) - PAD_Timeout - PAD_Timeout_Delay)
      if (round(time.time()*100) - PAD_Timeout - PAD_Timeout_Delay) > 0:
        PAD_Timeout=-1
        PAD_Actif=False
        PAD_Transition=PAD_Transition_duree
        TraiteEvenement("PAD_Inactif")
        # Lance("SliderActionSelection")
        if Debug: print("PAD Inactif")
  
  if slider_visible or PAD_Transition>0:
    
    # PAD_Transition=-PAD_Transition_duree # activation de -PAD_Transition_duree à 0, désactivation de +PAD_Transition_duree à 0

    if PAD_Transition<0: PAD_Transition=PAD_Transition+1
    if PAD_Transition>0: PAD_Transition=PAD_Transition-1
    CAMERA.reset()
    if slider_visible:
      CAMERA.position((0,0,-recul + (PAD_Transition / PAD_Transition_duree)*60))
    if not slider_visible:
      CAMERA.position((0,0,-recul - ((PAD_Transition_duree - PAD_Transition) / PAD_Transition_duree)*60))

    ############################ Slider ##############################
    # Prise en compte des déplacements
    if  slider_action=='DroiteSelection':
      if move_steps_media <= nb_step_media:
        i=0
        while (i < len(Medias)):
          if (i > current_media -3) and (i < current_media + 3):
            Media = Medias[i]
            x=(i-current_media-move_steps_media/nb_step_media)*distance_mediax
            y, z = 0, 0
            if i == (current_media+1):
              z=-(move_steps_media/nb_step_media)*distance_mediaz
            elif i == current_media:
              z=-(1-move_steps_media/nb_step_media)*distance_mediaz
            Media.media.position(x,y,z)
          i=i+1
      if move_steps_media == nb_step_media:
        slider_action = ''
        current_media = current_media + 1 
      else:
        move_steps_media=move_steps_media+1
              
              
    if slider_action == 'GaucheSelection':
      if move_steps_media <= nb_step_media:
        i=0
        while (i < len(Medias)):
          if (i > current_media -3) and (i < current_media + 3):
            Media = Medias[i]
            x=(i-current_media+move_steps_media/nb_step_media)*distance_mediax
            y, z = 0, 0
            if i == (current_media-1):
              z=-(move_steps_media/nb_step_media)*distance_mediaz
            elif i == current_media:
              z=-(1-move_steps_media/nb_step_media)*distance_mediaz
            Media.media.position(x,y,z)
          i=i+1
      if move_steps_media == nb_step_media:
        slider_action = ''
        current_media = current_media - 1 
      else:
        move_steps_media=move_steps_media+1

    if slider_action == 'AfficherCategoriesAvecChangementMedia':
        
        transitionMediaHaut(move_steps, nb_max_steps)
          
        if move_steps < nb_max_steps:
          move_steps=move_steps+1
        else:
          if Debug: print('AfficherCategoriesAvecChangementMedia')
          current_media = next_current_media
          Medias = NextMedias
          NextMedias = []
          slider_action = ''  
        
    
    if slider_action == 'HautCategories':
      if move_steps_cat <= nb_step_cat:
          i=0
          for cat in cats:
              y=(i-current_cat-move_steps_cat/nb_step_cat)*distance_caty
              z=-distance*(1.8-(abs(i-current_cat-move_steps_cat/nb_step_cat)*distance_catz))
              cat.position(0,y,z)
              i=i+1
          
          transitionMediaBas(move_steps_cat, nb_step_cat)
          
      if move_steps_cat < nb_step_cat:
        move_steps_cat=move_steps_cat+1
      else:
        current_cat = next_cat
        current_souscat = -1
        current_media = next_current_media
        Medias = NextMedias
        NextMedias = []
        slider_action = ''
        
    if slider_action == 'BasCategories':
      if move_steps_cat <= nb_step_cat:
        i=0
        for cat in cats:
          y=(i-current_cat+move_steps_cat/nb_step_cat)*distance_caty
          z=-distance*(1.8-(abs(i-current_cat+move_steps_cat/nb_step_cat)*distance_catz))
          cat.position(0,y,z)
          i=i+1
          
        #print("transitionMediaHaut")
        transitionMediaHaut(move_steps_cat, nb_step_cat)
          
      if move_steps_cat < nb_step_cat:
        move_steps_cat=move_steps_cat+1
      else:
        current_cat = next_cat
        current_souscat = -1
        current_media = next_current_media
        Medias = NextMedias
        NextMedias = []
        slider_action = ''  
        
    if slider_action=='AfficherSousCategories':
      # Afficher la transition des médias
      transitionMediaBas(move_steps, nb_step_groupe_media)
      
      # Afficher la transition à gauche de la catégorie
      cat = cats[current_cat]
      x=-2*move_steps/nb_step_groupe_media
      y=move_steps/nb_step_groupe_media
      z=-distance*1.8
      cat.position(x,y,z)
      
      if move_steps < nb_step_groupe_media:
        move_steps=move_steps+1
      else:
        current_media = next_current_media
        Medias = NextMedias
        NextMedias = []
        if Debug: print('dans le bloc if slider_action=="AfficherSousCategories", len(Medias) = ',len(Medias))
        slider_action = ''
        
    if slider_action=='HautSousCategories':
      if move_steps_souscat <= nb_step_souscat:
        i=0
        for souscat in souscats:
          y=(i-current_souscat-move_steps_souscat/nb_step_cat)*distance_caty
          z=-distance*(1.8-(abs(i-current_souscat-move_steps_souscat/nb_step_souscat)*distance_catz))
          souscat.position(0,y,z)
          i=i+1
          
        #print("transitionMediaBas")
        transitionMediaBas(move_steps_souscat, nb_step_souscat)
        
      if move_steps_souscat < nb_step_souscat:
        move_steps_souscat=move_steps_souscat+1
      else:
        current_souscat = next_souscat
        current_media = next_current_media
        Medias = NextMedias
        NextMedias = []
        slider_action = ''
        
    if slider_action=='BasSousCategories':
      if move_steps_souscat <= nb_step_souscat:
        i=0
        for souscat in souscats:
          y=(i-current_souscat+move_steps_souscat/nb_step_souscat)*distance_caty
          z=-distance*(1.8-(abs(i-current_souscat+move_steps_souscat/nb_step_souscat)*distance_catz))
          souscat.position(0,y,z)
          i=i+1
          
        #print("transitionMediaHaut")
        transitionMediaHaut(move_steps_souscat, nb_step_souscat)
          
      if move_steps_souscat < nb_step_souscat:
        move_steps_souscat=move_steps_souscat+1
      else:
        current_souscat = next_souscat
        current_media = next_current_media
        Medias = NextMedias
        NextMedias = []
        slider_action = ''
        
    ######################################################################    
    # Affichage des objets    
  
    # Affichage de la fleche et du cadre si slider_mode = catégorie
    if (slider_mode == 'categorie') and (action == ''):
      fleche.draw()
    
    
    if slider_mode=='categorie':
      cadre.draw()
      for cat in cats:
        cat.draw()
        
    
    if slider_mode=='souscategorie':
      cadre.draw()
      cat=cats[current_cat]
      cat.draw()
      for souscat in souscats:
        souscat.draw()
      if slider_action=='':
        fleche.draw()
        
   
    if slider_mode == 'categorie' and Blur:
      defocus.start_blur()
    
    
    # Afficher 2 médias avant et 2 médias après le media courant
    i=0
    while (i < len(Medias)):
      if (i > current_media -2) and (i < current_media + 2):
        Media = Medias[i]
        Media.media.draw()
      i=i+1
    
    # idem pour Next Medias
    i=0
    while (i < len(NextMedias)):
      if (i > next_current_media -2) and (i < next_current_media + 2):
        Media = NextMedias[i]
        Media.media.draw()
      i=i+1
      
    # Afficher le texte du média courant
    if (slider_mode=='selection') and (slider_action==''):
      Media = Medias[current_media]
      Media.mediadesc.position(0,0,-distance*1.8)
      Media.mediadesc.draw()      
    
    # Afficher la catégorie et la sous catégorie en haut à gauche
    if (slider_mode=='selection') and (len(cats2) > 0):
      cats2[current_cat].position(-2,1,-distance*1.8)
      cats2[current_cat].draw()
      if current_souscat != -1:
        souscats2[current_cat][current_souscat].position(-2,0.5,-distance*1.8)
        souscats2[current_cat][current_souscat].draw()
      
    if Fog:
      if move_steps_cat==2:
        if Debug: print("Fog")
      if (slider_mode == 'categorie') or (slider_mode == 'souscategorie'):
        for i in range(len(Medias)):
          if i==current_media:
            Medias[i].media.set_fog((0,0,0,0.9),30.0)
          else:
            Medias[i].media.set_fog((0,0,0,0.92),40.9)
        for i in range(len(NextMedias)):
          if i==next_current_media:
            NextMedias[i].media.set_fog((0,0,0,0.9),30.0)
          else:
            NextMedias[i].media.set_fog((0,0,0,0.92),40.9)
       
        #if current_media > 1:
          #Medias[current_media-2].media.set_fog((0,0,0,0.92),40.9)
        #if current_media > 0:
          #Medias[current_media-1].media.set_fog((0,0,0,0.92),40.9)
        #Medias[current_media].media.set_fog((0,0,0,0.9),30.0)
        #if current_media < nb_images-1:
          #Medias[current_media+1].media.set_fog((0,0,0,0.92),40.9)
        #if current_media < nb_images-2:
          #Medias[current_media+2].media.set_fog((0,0,0,0.92),40.9)

      else:
        for Media in Medias:
          Media.media.set_fog((0,0,0,1),100)
        for Media in NextMedias:
          Media.media.set_fog((0,0,0,1),100)

    if Blur:
      if move_steps_cat==2:
        if Debug: print("Blur")
      if slider_mode == 'categorie':
        defocus.end_blur()
        for Media in Medias:
          defocus.blur(Media.media, -distance/2, distance, 2) # if 4,9,5 : 4 is focal distance, >= 9 distance will get 5 x blurring, nearer than focus also blurs
        for Media in NextMedias:
          defocus.blur(Media.media, -distance/2, distance, 2) # if 4,9,5 : 4 is focal distance, >= 9 distance will get 5 x blurring, nearer than focus also blurs
        fleche.position(0,0,-39)
        fleche.draw()
  
    # Slider timeout
    slider_timeout = slider_timeout-1
    if (slider_timeout % 10) == 0:
      if Debug: print('slider_timeout = ',slider_timeout)
    if slider_timeout <= 0: SliderTimeout()
  
    """
    hand.rotateToY(110)
    #hand.rotateIncY(3)
    hand.rotateToX(-80)
    #hand.rotateIncX(3)
    hand.rotateToZ(10)
    #hand.rotateIncZ(1)
    hand.position(10,-7+move_steps/6,-19)
    #hand.position(0,-1,-32)
    
    #hand.position(10,-6+move_steps/2,40)
    
    hand.draw()

    #sprite.rotateToX(20)
    sprite.position(14,-7.5,-10)
    sprite.draw()
    
    """
# action qui detruit le pi3D dans le scenario
  if slider_stop==True:
      #mykeys.close()
      DISPLAY.destroy()
      break
   
  # Timeline
  if PlayedMediaId :
    try:
        position=int(round(Player.position()*10))
        for event_time in MediaTimeline:
            if position==int(event_time):
                for actionid in MediaTimeline[event_time]:
                    Lance(actionid)
                MediaTimeline.pop(event_time, None)
    except:
        pass
        
GPIO.cleanup()

if RS232_ok:
    RS232.close()
if RS232_2_ok:
    RS232_2.close()

print("******************")
print("***** Terminé ****")
print("******************")

