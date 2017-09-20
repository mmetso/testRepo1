#!/usr/bin/python3

import pifacedigitalio #for digital io card control
import pygame.mixer #for playing wav sound files
import random #to generate random numbers
from time import sleep
import time #for sleep and time&date print
import os #to search for .wav files in dedicated folder
import sys #for command line arguments
import urllib.request #to read html data from the web
import json #to parse json format
import os #to use espeak and for directory existence checking
import logging #to log errors
import datetime #for the error log

logging.basicConfig(filename='/home/pi/python/errorLog.txt',level=logging.DEBUG)

# get the total number of args passed to this .py
total = len(sys.argv)

print ("the total numbers of args passed to the script: %d " % total)
print ("script name: %s" % str(sys.argv[0]))
print ("script length in seconds: %s" % str(eval(sys.argv[1])))

def setSoundLevel(percentage):
#  os.system('amixer cset numid=1 "{0}"'.format(percentage)) #for native audio
  #for usb audio output
  os.system('amixer -c 0 sset "Headphone",0 "{0}"'.format(percentage))

def doorOutClosed():
    return pifacedigitalio.digital_read(0)

def pirTriggered():
    return pifacedigitalio.digital_read(1)

def say(something):
#  os.system('espeak -ven-us+f2 -s150 "{0}"'.format(something)) #us english
  os.system('espeak -vfi+f2 -s150 "{0}"'.format(something)) #finnish

def getTemperature():
  #to search for a station, in tapiola f ex:
  #http://autocomplete.wunderground.com/aq?query=tapiola
  #kaisaniemi
#  request = 'http://api.wunderground.com/api/53b93f105317f6a4/conditions/q/zmw:00000.4.02978.json'
  #malmi
#  request = 'http://api.wunderground.com/api/53b93f105317f6a4/conditions/q/zmw:00000.3.WEFHF.json'
  #otaniemi
#  request = 'http://api.wunderground.com/api/53b93f105317f6a4/conditions/q/60.18,24.82.json'
  #lahela
  request = 'http://api.wunderground.com/api/53b93f105317f6a4/conditions/q/60.40,24.98.json'
  try:
    response = urllib.request.urlopen(request)
  except urllib.error.URLError as e:
    logging.exception('unresponsive url')
    return 100
  content = response.read()
  data = json.loads(content.decode('utf8'))
  try:
    temperature = int(round(data.get('current_observation').get('temp_c')))
  except Exception as e:
    logging.exception('current_observation value not available for conversion')
    temperature = 100
  print ('current temperature in celsius: ' + str(temperature))
  return temperature

def loadTemperatureSound(temperature):
  temperatureWavFileNames = []
  temperaturePath = '/home/pi/wav/temperature/t' + str(temperature)
  print(temperaturePath)
  if os.path.exists(temperaturePath):
    #search for and list .wav files in the correct temperature dir
    for root, dirs, files in os.walk(temperaturePath):
      for file in files:
        if file.endswith(".wav"):
          temperatureWavFileNames.append(os.path.join(root, file))
    soundIndex = random.randint(0,len(temperatureWavFileNames)-1)
    print (str(temperatureWavFileNames[soundIndex]))
    pygame.mixer.music.load(temperatureWavFileNames[soundIndex])
    return 1 #return 1 when wav sound exists, otherwise 0
  else:
    return 0

def loadWeekdaySound(weekday):
  weekdayWavFileNames = []
  weekdayPath = '/home/pi/wav/weekday/' + str(weekday)
  print(weekdayPath)
  if os.path.exists(weekdayPath):
    #search for and list .wav files in the correct weekday dir
    for root, dirs, files in os.walk(weekdayPath):
      for file in files:
        if file.endswith(".wav"):
          weekdayWavFileNames.append(os.path.join(root, file))
    soundIndex = random.randint(0,len(weekdayWavFileNames)-1)
    print (str(weekdayWavFileNames[soundIndex]))
    pygame.mixer.music.load(weekdayWavFileNames[soundIndex])
    return 1 #return 1 when wav sound exists, otherwise 0
  else:
    return 0

if __name__ == "__main__":
  try:
    timeNow = time.time()
    scriptStartTime = timeNow
    activityIndoorsEventTime = timeNow - 1000 #a long ago
    doorOutEventTime = timeNow - 1000 #a long ago
    messageEventTime = timeNow
    goodByeClauseOneTime = timeNow - 1000 #a long ago

    DELAY = 0.1  # seconds between processing rounds

    #update sound settings
    with open("/home/pi/python/soundSettings.txt", "r") as ins:
      content = ins.read().splitlines()
    if (content[0] == '1'):
      soundsOn = True
    else:
      soundsOn = False
#    soundsOn = True #set to 1 to output audio
    print ('sounds on setting: ' + str(soundsOn))

    weekdaySilenceStop = 630#0
    weekdaySilenceStart = 2059#2359
    weekendSilenceStop = 645#0
    weekendSilenceStart = 2059#2359

    sayGoodByeClauseTwo = False

    #note: silence times override sound weakness settings
    weekdayWeakSoundStopTime = 725
    weekdayWeakSoundStartTime = 2030
    weekendWeakSoundStopTime = 900
    weekendWeakSoundStartTime = 2030
    weak = 0
    strong = 1

    soundLevel = strong
    setSoundLevel('80%')
    print ('sound level is set to strong')

    noDoorEvent = 0
    doorGotOpened = 1
    doorGotClosed = 2

    pifacedigitalio.init()

    temperatureNow = getTemperature()
    weatherUpdateTime = timeNow

    pygame.mixer.init(44000, -16, 1, 1024)

    thanksWavFileNames = []
    #search for and list .wav files in the following dir
    for root, dirs, files in os.walk('/home/pi/wav/thanks/'):
      for file in files:
        if file.endswith(".wav"):
          thanksWavFileNames.append(os.path.join(root, file))
    welcomeWavFileNames = []
    #search for and list .wav files in the following dir
    for root, dirs, files in os.walk('/home/pi/wav/welcome/'):
      for file in files:
        if file.endswith(".wav"):
          welcomeWavFileNames.append(os.path.join(root, file))
    goodByeWavFileNames = []
    #search for and list .wav files in the following dir
    for root, dirs, files in os.walk('/home/pi/wav/goodBye/'):
      for file in files:
        if file.endswith(".wav"):
          goodByeWavFileNames.append(os.path.join(root, file))
    closeDoorInWavFileNames = []
    #search for and list .wav files in the following dir
    for root, dirs, files in os.walk('/home/pi/wav/closeDoorIn/'):
      for file in files:
        if file.endswith(".wav"):
          closeDoorInWavFileNames.append(os.path.join(root, file))
    closeDoorOutWavFileNames = []
    #search for and list .wav files in the following dir
    for root, dirs, files in os.walk('/home/pi/wav/closeDoorOut/'):
      for file in files:
        if file.endswith(".wav"):
          closeDoorOutWavFileNames.append(os.path.join(root, file))

    f = open('/home/pi/python/log.txt', 'a')
#    text = 'door watch program started at: ' + time.strftime("%d.%m.%Y %H:%M:%S")
#    f.write(text + '\n')

    pirTriggeredPrev = pirTriggered()
    sleep(DELAY)
    doorOutClosedPrev = doorOutClosed()
    sleep(DELAY)

    pirTriggeredCurr = pirTriggeredPrev
    doorOutClosedCurr = doorOutClosedPrev

    activityIndoors = 1
    activityIndoorsPrev = 1
    activityIndoorsCurr = 1

    pollingDoorOut = False
    doorCloseRequestGiven = False

    print ('program running!\n')

    while True:
      timeNow = time.time()
      hrsMins = int(time.strftime("%H%M"))
      #include friday in definition of weekend
      if int(time.strftime('%w')) == 5 or int(time.strftime('%w')) == 6 or int(time.strftime('%w')) == 0: weekend = True
      else: weekend = False

      if (weekend == False and (hrsMins >= weekdayWeakSoundStartTime or hrsMins <= weekdayWeakSoundStopTime) and soundLevel == strong) or \
         (weekend == True and (hrsMins >= weekendWeakSoundStartTime or hrsMins <= weekendWeakSoundStopTime) and soundLevel == strong):
        soundLevel = weak
#        setSoundLevel('60%') #for native audio output
        setSoundLevel('15%')
        print ('set level to weak')
      elif (weekend == False and (hrsMins > weekdayWeakSoundStopTime and hrsMins < weekdayWeakSoundStartTime) and soundLevel == weak) or \
           (weekend == True and (hrsMins > weekendWeakSoundStopTime and hrsMins < weekendWeakSoundStartTime) and soundLevel == weak):
        soundLevel = strong
        setSoundLevel('80%')
        print ('set level to strong')

      if timeNow - scriptStartTime > eval(sys.argv[1]): #run for specified time
        break

      #if weather data (temperature) was not updated within the last 14 minutes,
      #do it.
      if timeNow - weatherUpdateTime > 14*60:
        temperatureNow = getTemperature()

        #also play dummy sound to keep usb audio alive.
        pygame.mixer.music.load('/home/pi/wav/special/empty.wav')
        pygame.mixer.music.play()

        #also update sound settings at the same time
        with open("/home/pi/python/soundSettings.txt", "r") as ins:
          content = ins.read().splitlines()
        if (content[0] == '1'):
          soundsOn = True
        else:
          soundsOn = False
        print ('sounds on setting: ' + str(soundsOn))

        weatherUpdateTime = timeNow

      if pollingDoorOut == False:
        pirTriggeredCurr = pirTriggered()
        if (pirTriggeredCurr != 1 and pirTriggeredPrev == 1):#activity indoors
          activityIndoors = 0
          activityIndoorsStartTime = timeNow
        #if 92 seconds passed without activity, consider it being no activity
        elif (activityIndoors == 0 and timeNow - activityIndoorsStartTime > 92):
          activityIndoors = 1
        activityIndoorsCurr = activityIndoors

        if (activityIndoorsCurr != 1 and activityIndoorsPrev == 1): #activity indoors
          activityIndoorsEvent = doorGotOpened
          activityIndoorsEventTime = timeNow
          text = str(round(time.time(),2)) + ' activity indoors at ' + time.strftime("%d.%m.%Y %H:%M:%S")
          f.write(text + '\n')
          f.flush()
        elif (activityIndoorsCurr == 1 and activityIndoorsPrev != 1): #no more activity indoors
          activityIndoorsEvent = doorGotClosed
          activityIndoorsEventTime = timeNow
          text = str(round(time.time(),2)) + ' activity indoors stopped at ' + time.strftime("%d.%m.%Y %H:%M:%S")
          f.write(text + '\n')
          f.flush()
        else:
          activityIndoorsEvent = noDoorEvent
      else:
        activityIndoorsEvent = noDoorEvent

      if pollingDoorOut == True:
        doorOutClosedCurr = doorOutClosed()
        if (doorOutClosedCurr != 1 and doorOutClosedPrev == 1): #doorOut got opened
          doorOutEvent = doorGotOpened
          doorOutEventTime = timeNow
          text = str(round(time.time(),2)) + ' doorOutGotOpened at ' + time.strftime("%d.%m.%Y %H:%M:%S")
          f.write(text + '\n')
          f.flush()
        elif (doorOutClosedCurr == 1 and doorOutClosedPrev != 1): #doorOut got closed
          doorOutEvent = doorOutClosed
          doorOutEventTime = timeNow
          text = str(round(time.time(),2)) + ' doorOutGotClosed at ' + time.strftime("%d.%m.%Y %H:%M:%S")
          f.write(text + '\n')
          f.flush()
        else:
          doorOutEvent = noDoorEvent
      else:
        doorOutEvent = noDoorEvent

      print (str(activityIndoorsCurr) + ' ' + str(doorOutClosedCurr) + ' ' + str(timeNow))
#      print ('.', end=''); sys.stdout.flush()

#     1) thank you (for closing doors) message
#        = door close request was given and doorOut is closed
      if doorCloseRequestGiven == True and doorOutClosedCurr == 1:
        soundIndex = random.randint(0,len(thanksWavFileNames)-1)
        print (str(thanksWavFileNames[soundIndex]))
        pygame.mixer.music.load(thanksWavFileNames[soundIndex])
        if soundsOn == True:# and \
          #((weekend == False and hrsMins > weekdaySilenceStop and hrsMins < weekdaySilenceStart) or \
          # (weekend == True and hrsMins > weekendSilenceStop and hrsMins < weekendSilenceStart)):
          pygame.mixer.music.play()
        doorCloseRequestGiven = False

#     2) good bye message
#       = activity occurs indoors and doorOut is closed and time - doorOutEventTime > 10
      elif activityIndoorsEvent == doorGotOpened and doorOutClosedCurr == 1 and \
         (timeNow - doorOutEventTime > 10):
        text = time.strftime("%d.%m.%Y %H:%M:%S")
        print (text)
        if soundsOn == True and \
          ((weekend == False and hrsMins > weekdaySilenceStop and hrsMins < weekdaySilenceStart) or \
           (weekend == True and hrsMins > weekendSilenceStop and hrsMins < weekendSilenceStart)):
           #if proper wav file exists (function returns 1), load it and play
           if (loadTemperatureSound(temperatureNow) == 1):
             pygame.mixer.music.play()
           #else, play synthesized sound
           else:
             if temperatureNow > 0:
               say('lämpötila plus' + str(temperatureNow) + ' astetta.')
             elif temperatureNow < 0:
               say('lämpötila miinus' + str(0-temperatureNow) + ' astetta.')
             else:
               say('lämpötila' + temperatureNow + ' astetta.')
           goodByeClauseOneTime = timeNow
           sayGoodByeClauseTwo = True
        doorCloseRequestGiven = False

#    3) if good bye sound was recently played, continue with another clause
      elif sayGoodByeClauseTwo == True:
        #tell time if doorIn was opened and then rapidly closed
        if (timeNow - goodByeClauseOneTime < 1) and \
           (pirTriggeredCurr == 1):
          #first play empty wav to cancel out previous wav
          pygame.mixer.music.load('/home/pi/wav/special/empty.wav')
          pygame.mixer.music.play()
          say('kello on ' + time.strftime("%H:%M"))
          sayGoodByeClauseTwo = False
        #else, say a second clause if the last one was for goodbye and 8 seconds
        #have passed after the goodByeClauseOneTime
        elif (timeNow - goodByeClauseOneTime > 8):
          if hrsMins < 1813:
            #if proper wav file exists (function returns 1), load it and play
            if (loadWeekdaySound(int(time.strftime('%w'))) == 1):
              pygame.mixer.music.play()
            else:
              if random.randint(1,2) == 1:
                soundIndex = random.randint(0,len(goodByeWavFileNames)-1)
                print (str(goodByeWavFileNames[soundIndex]))
                pygame.mixer.music.load(goodByeWavFileNames[soundIndex])
                pygame.mixer.music.play()
          elif hrsMins > 2030:
            pygame.mixer.music.load('/home/pi/wav/special/markusRautioToivotammeHyvaaYota.wav')
            pygame.mixer.music.play()
          else:
            if random.randint(1,2) == 1:
              soundIndex = random.randint(0,len(goodByeWavFileNames)-1)
              print (str(goodByeWavFileNames[soundIndex]))
              pygame.mixer.music.load(goodByeWavFileNames[soundIndex])
              pygame.mixer.music.play()
          sayGoodByeClauseTwo = False

#     4) welcome message
#        = activity occurs indoors and doorOut is open and time - doorOutEventTime < 10
      elif activityIndoorsEvent == doorGotOpened and doorOutClosedCurr == 0 and \
         (timeNow - doorOutEventTime < 10):
        sleep(10) #door got opened. wait a bit before audio output
        soundIndex = random.randint(0,len(welcomeWavFileNames)-1)
        print (str(welcomeWavFileNames[soundIndex]))
        pygame.mixer.music.load(welcomeWavFileNames[soundIndex])
        if soundsOn == True and \
          ((weekend == False and hrsMins > weekdaySilenceStop and hrsMins < weekdaySilenceStart) or \
           (weekend == True and hrsMins > weekendSilenceStop and hrsMins < weekendSilenceStart)):
          pygame.mixer.music.play()
        doorCloseRequestGiven = False

#     5) close doorOut message repeating once every 30s
#        = doorOut is open and time - doorOutEventTime > 20 and
#          time - messageEventTime > 30
      elif doorOutClosedCurr == 0 and \
           (timeNow - doorOutEventTime > 20) and \
           (timeNow - messageEventTime > 30):
        soundIndex = random.randint(0,len(closeDoorOutWavFileNames)-1)
        print (str(closeDoorOutWavFileNames[soundIndex]))
        pygame.mixer.music.load(closeDoorOutWavFileNames[soundIndex])
        if soundsOn == True:# and \
          #((weekend == False and hrsMins > weekdaySilenceStop and hrsMins < weekdaySilenceStart) or \
          # (weekend == True and hrsMins > weekendSilenceStop and hrsMins < weekendSilenceStart)):
          pygame.mixer.music.play()
          doorCloseRequestGiven = True
        messageEventTime = timeNow

      elif activityIndoorsEvent == doorGotClosed:
        print ('activity indoors stopped at ' + time.strftime("%d.%m.%Y %H:%M:%S"))
      elif doorOutEvent == doorGotClosed:
        print ('door out closed at ' + time.strftime("%d.%m.%Y %H:%M:%S"))
      elif activityIndoorsEvent == doorGotOpened:
        print ('activity indoors started at ' + time.strftime("%d.%m.%Y %H:%M:%S"))
      elif doorOutEvent == doorGotOpened:
        print ('door out opened at ' + time.strftime("%d.%m.%Y %H:%M:%S"))

      pirTriggeredPrev = pirTriggeredCurr
      activityIndoorsPrev = activityIndoorsCurr
      doorOutClosedPrev = doorOutClosedCurr

      sleep(DELAY)

      if pollingDoorOut == True:
        pollingDoorOut = False
      else:
        pollingDoorOut = True

#    text = 'door watch program stopped at timed mark: ' + time.strftime("%d.%m.%Y %H:%M:%S")
#    f.write(text + '\n')
    f.close()
    print ('\nprogram stopped as planned.\n')
  except Exception as e:
    logging.exception("Something awful happened!")

#  logging.debug("Finishing main!")
  #except:
  #  now = datetime.datetime.now()	
  #  logging.exception(str(now)) 
