#Purpose: This is a MQTT client designed for a Raspberry Pi 3B+ which is responsible for audio analysis.  
#         It identifies LoZ songs and publishes messages on those topics.  

#Code for audio analysis was originally taken from
#https://benchodroff.com/2017/02/18/using-a-raspberry-pi-with-a-microphone-to-hear-an-audio-alarm-using-fft-in-python/
#then further adapted from Allen Pan's (Sufficiently Advanced) code
#https://github.com/Sufficiently-Advanced/ZeldaHomeAutomation/blob/master/zelda_home_public.py
import pyaudio
import numpy as np
from numpy import zeros,linspace,short,fromstring,hstack,transpose,log
from scipy.fftpack import fft
from time import sleep
from collections import deque
import paho.mqtt.client as mqtt
import requests
import pygame.mixer
from pygame.mixer import Sound

#mqtt setup
client = mqtt.Client()
client.connect("localhost",1883,300)

#audio output setup
pygame.mixer.init(32000)
confirm = Sound("Music/OOT_Song_Correct.wav")

#audio analysis setup
#audio sampler setup
freqNow = 1.0 #current and previous frequencies measured
freqPast = 1.0
NUM_SAMPLES = 2048
SAMPLING_RATE = 48000
pa = pyaudio.PyAudio()
_stream = pa.open(format=pyaudio.paInt16,channels=1, rate=SAMPLING_RATE,input=True,frames_per_buffer=NUM_SAMPLES)

#Volume Sensitivity (0 = max, 1 = min)
SENSITIVITY= 1.0

# Note peak frequencies
# These must be tuned via audacity (record audio then analyze -> plot spectrum)
D4 = 586
E = 685
F = 752
G = 806
A = 882
B = 994
D5 = 1178
# Note ranges based on note frequencies
BANDWIDTH = 25 #bandwidth is the margin of error of frequencies accepted for that note
minD4 = D4-50
maxD4 = D4+BANDWIDTH
minE = E-BANDWIDTH
maxE = E+BANDWIDTH
minF = F-40
maxF = F+BANDWIDTH
minG = G-BANDWIDTH
maxG = G+BANDWIDTH
minA = A-BANDWIDTH
maxA = A+55
minB = B-BANDWIDTH
maxB = B+BANDWIDTH
minD5 = D5-BANDWIDTH
maxD5 = D5+BANDWIDTH

# Song note sequences
sun = deque(['A','E','D5','A','E','D5'])
time = deque(['A','D4','E','A','D4','E'])
fire = deque(['E','D4','E','D4','A','E']) 
storm = deque(['D4','E','D5','D4','E','D5'])
saria = deque(['E','A','B','E','A','B'])
notes = deque(['G','G','G','G','G','G'], maxlen=6)

print ("")
print ("")
print ("The above errors are totally normal and expected parts of using pyaudio on a Raspberry pi.")
print ("They cause no functional problems and therefore have not been fixed.")
print ("")
print ("")

#Purpose: To calculate the frequencies
#Side effect: Updates freqNow and freqPast with current and previous frequencies
def calcFreq():
    global freqNow
    global freqPast
    while _stream.get_read_available()< NUM_SAMPLES: sleep(0.01)
    audio_data = np.frombuffer(_stream.read(_stream.get_read_available()), dtype=np.int16)[-NUM_SAMPLES:]
    normalized_data = audio_data / 32768.0 # Each data point is a signed 16 bit number, so we can normalize by dividing 32*1024
    intensity = abs(fft(normalized_data))[:NUM_SAMPLES//2]
    frequencies = linspace(0.0, float(SAMPLING_RATE)/2, num=int(NUM_SAMPLES/2))
    which = intensity[1:].argmax()+1
    if which != len(intensity)-1:     
        # use quadratic interpolation around the max
        y0,y1,y2 = log(intensity[which-1:which+2:])
        x1 = (y2 - y0) * .5 / (2 * y1 - y2 - y0)
        freqPast = freqNow
        freqNow = (which+x1)*SAMPLING_RATE/NUM_SAMPLES
    else:
        freqNow = which*SAMPLING_RATE/NUM_SAMPLES

#Purpose: Determine if freqNow and freqPast indicate a note is being played
#Side effect: Updates notes double ended queue with appropriate note
def checkNote():
       #For speed check if the frequency is within the range of any of the notes (d4 to d5)
    #   and require that the note has been held constant for two cycles (filters out noise).
    if minD4 <= freqPast <= maxD5 and abs(freqNow-freqPast) <= 25:
        #Check for each note individually
        if minA<=freqPast<=maxA and minA<=freqNow<=maxA and notes[-1]!='A':
            notes.append('A')
            print ("You played A!")
        elif minF<=freqPast<=maxF and minF<=freqNow<=maxF and notes[-1]!='F':
            notes.append('F')
            print ("You played F!")
        elif freqPast <= maxD4 and minD4 <= freqNow <= maxD4 and notes[-1]!='D4':
            notes.append('D4')
            print ("You played D4!")
        elif minD5 <= freqPast <= maxD5 and minD5 <= freqNow <= maxD5 and notes[-1]!='D5':
            notes.append('D5')
            print ("You played D5!")
        elif minB<=freqPast<=maxB and minB<=freqNow<=maxB and notes[-1]!='B':
            notes.append('B')
            print ("You played B!")
        elif minE<=freqPast<=maxE and minE<=freqNow<=maxE and notes[-1]!='E':
            notes.append('E')
            print ("You played E!")
        elif minG<=freqPast<=maxG and minG<=freqNow<=maxG and notes[-1]!='G':
            notes.append('G')
            print ("You played G!")
        elif notes[-1]!='A' and notes[-1]!='F' and notes[-1]!='D4' and notes[-1]!='D5' and notes[-1]!='B' and notes[-1]!='E' and notes[-1]!='G':
            print ("Invalid Note")#For simplicity we will not append repeat notes and only flag invalid notes (in range)

#Purpose: If the notes queue equals any of the song queues then trigger the effect
# This either publishes a message using MQTT or performs a HTTP request to the IFTTT service.
def checkSong():
    if notes==sun:
        print ("Sun song!")
        client.publish("songID", "1") #1=Sun
        confirm.play()
        notes.append('G')#append with 'G' to 'reset' notes, this keeps the song from triggering constantly
    if notes==time:
        print ("song of Time!")
        client.publish("songID", "2") #2=Time
        confirm.play()
        notes.append('G')     
    if notes==fire:
        print ("Bolero of fire!")
        client.publish("songID", "3") #3=Fire
        confirm.play()
        notes.append('G')    
    if notes==storm:
        print ("song of Storms!")
        client.publish("songID", "4") #4=Storm
        confirm.play()
        notes.append('G')
    if notes==saria:
        print ("Saria's song!") #5=Saria
        _stream.stop_stream()
        requests.post("https://maker.ifttt.com/trigger/call/with/key/bkUoRggtc6mA2OeiBa6kv25sx_TugR8YNFXMwQdcqk")
        notes.append('G')
        confirm.play()
        _stream.start_stream()

while True:
    calcFreq()
    checkNote()
    checkSong()
