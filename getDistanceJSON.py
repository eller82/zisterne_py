#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Entfernungsmesser für RaspberryPi
# Version 1.1
#
# Copyright: tfnApps.de Jens Dutzi
# Datum: 27.06.2015
# Lizenz: MIT Lizenz (siehe LICENSE)
# -----------------------------------
# Changed by André Mellentin to calculate the volume in liter
# Datum: 23.07.2016 
# www.dreamyourworld.de 
# Lizenz: MIT Lizenz (siehe LICENSE)
# -----------------------------------

# import required modules
import requests
import json
import time
import datetime
#import ftplib
#import pysftp
import RPi.GPIO as GPIO

# define GPIO pins
GPIOTrigger = 18
GPIOEcho    = 24

# define required variables 
total = 0
Mittelwert = 0
voll=90  # 90 cm von Sensor bis Wasseroberfläche = voll
leer=234 # 255 cm von Sensor bis Wasseroberfläche = leer
# 255cm (bis Oberkannte) - 30cm (oberkante bis sensor)

# Funktion zum messen der Entfernung
def MesseDistanz():
	# Trigger auf "high" setzen (Signal senden)
	GPIO.output(GPIOTrigger, True)

	# Signal für 10µs senden (ggf. je nach RaspberryPi auf 0.0005 setzen)
	time.sleep(0.00001)
	
	# Trigger auf "low setzen (Signal beenden)
	GPIO.output(GPIOTrigger, False)

	# Aktuelle Zeit setzen
	StartZeit = time.time()
	StopZeit = StartZeit

	# Warte bis "Echo" auf "low" gesetzt wird und setze danach Start-Zeit erneut
	while GPIO.input(GPIOEcho) == 0:
		StartZeit = time.time()

	# Warte bis "Echo" auf "high" wechselt (Signal wird empfangen) und setze End-Zeit
	while GPIO.input(GPIOEcho) == 1:
		StopZeit = time.time()

	# Abstand anhand der Signal-Laufzeit berechnen
	# Schallgeschwindigkeit: 343,50 m/s (bei 20°C Lufttemperatur)
	# Formel: /Signallaufzeit in Sekunden * Schallgeschwindigket in cm/s) / 2 (wg. Hin- und Rückweg des Signals)
	SignalLaufzeit = StopZeit - StartZeit
	Distanz = (SignalLaufzeit/2) * 34350
	
	return [Distanz, (SignalLaufzeit*1000/2)]

# main function
def main():
	try:

		total = 0
		count = 0
		for i in range(0,10):
			Ergebnis = MesseDistanz()
			if Ergebnis[0] > leer:
				print("Gemessene Entfernung: %.1f cm (Signallaufzeit: %.4fms)" % (Ergebnis[0], Ergebnis[1]))
				print "Fehler in Messung"
				break
			else:
				total = total + Ergebnis[0]
				count += 1
				print("Gemessene Entfernung: %.1f cm (Signallaufzeit: %.4fms)" % (Ergebnis[0], Ergebnis[1]))
				time.sleep(1)

		GPIO.cleanup()

		# Ermittle Mittelwert
		Mittelwert = total/count

		print "Mittelwert: ", Mittelwert
		#check für volle Zisterne
                #Mittelwert = Mittelwert - 30

		# Ermittle Füllstand
		liter_pro_cm=3.1415*100*100*1/1000  #pi * radius * radius * 1cm /1000 sonst milliliter
		volumen=(leer-Mittelwert)*liter_pro_cm

		print "Volumen: ", volumen

		ts = time.time()
		sttime = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

		# Speichere Mittelwert auf RaspberryPi
		f1=open('/home/pi/development/messung/entfernung.txt','a')
		f1.write(sttime + ';' + str(round(Mittelwert,2)) + ';\n')
		f1.close()
 
 		# Speichere Füllstand auf RaspberryPi
		f2=open('/home/pi/development/messung/volumen.txt','a')
		f2.write(sttime + ';' + str(round(volumen,2)) + ';\n')
		f2.close()
 
 		# Übertrage Files auf remote Server zur weiteren Verarbeitung
		f1l=open('/home/pi/development/messung/entfernung.txt','r')
		f2l=open('/home/pi/development/messung/volumen.txt','r')
		
		#url = "http://192.168.2.160:3000/api/v1/posts/create"
		url = "http://zisterne.mellentin.eu/api/v1/posts/create"
	
		data= {}
		data['volumen'] = {}
		data['volumen']['volumen'] = str(round(volumen,2))
		data['volumen']['messdatum'] = sttime

		data['entfernung'] = {}
		data['entfernung']['entfernung'] = str(round(Mittelwert,2))
		data['entfernung']['messdatum'] = sttime

		json_data = json.dumps(data)
		print json_data
		#headers = {'Content-type': 'application/json', 'Accept': 'text/plain', 'X-USER-TOKEN': 'MC2DkLJaj2f57GBxmgKERfmC'}
		headers = {'Content-type': 'application/json', 'Accept': 'text/plain', 'X-USER-TOKEN': 'rXiFiDWmCECEnsfv65hi6BVY'}
	
		if volumen < 8000:
			r = requests.post(url, data=json.dumps(data), headers=headers)
			print r.status_code
		else:
			print "Fehler in Berechnung"
		
		#cnopts = pysftp.CnOpts()
		#cnopts.hostkeys = None    # disable host key checking.
		#pysftp.cnopts.hostkeys.load('~/.ssh/known_host')
		
		#serverftp = pysftp.Connection('melle.monoceres.uberspace.de', username ='melle', password='HO0v45RBi2XL5aT')
		#serverftp = pysftp.Connection(host='melle.monoceres.uberspace.de', port=22, username ='melle', password='HO0v45RBi2XL5aT')

		#serverftp.cwd("/home/melle/zisterne/public/")
		#serverftp.storbinary('Stor entfernung.txt', f1l)
		#serverftp.put('/home/pi/development/messung/entfernung.txt')
		#serverftp.put('/home/pi/development/messung/volumen.txt')
		#serverftp.storbinary('Stor volumen.txt', f2l)
		#serverftp.close()

	# reset GPIO settings if user pressed Ctrl+C
	except KeyboardInterrupt:
		print("Messung abgebrochen")
		GPIO.cleanup()

if __name__ == '__main__':
	# benutze GPIO Pin Nummerierung-Standard (Broadcom SOC channel)
	GPIO.setmode(GPIO.BCM)

	# Initialisiere GPIO Ports
	GPIO.setup(GPIOTrigger, GPIO.OUT)
	GPIO.setup(GPIOEcho, GPIO.IN)

	# Setze GPIO Trigger auf false
	GPIO.output(GPIOTrigger, False)

	# Main-Funktion starten
	main()
