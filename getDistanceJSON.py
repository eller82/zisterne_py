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
	
def MesseDistanz10():
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

	# Ermittle Mittelwert
	Mittelwert = total/count
	
	return Mittelwert

# main function
def main():
	try:

		Mittelwert = MesseDistanz10()

		print "Mittelwert: ", Mittelwert
		
		#öffne die Datei mit der zuletzt ermittelten Entfernung und lese den letzten Datensatz
		f=open('/home/pi/development/messung/entfernung.txt', 'r')
		if f.mode == 'r':
			lines = f.read().splitlines()
			last_line = lines[-1]
			ll = last_line
		f.close
	
		entfernung = ll.split(";")
		l_entfernung = entfernung[1]
	
		#wenn die letzte Entfernung mehr als 1cm von dem aktuellen Wert abweicht, mache noch eine Messung
		#hiermit sollen größere Messabweichungen vermieden werden
		unterschied = float(l_entfernung) - float(Mittelwert)

		if unterschied > 1 or unterschied < -1:
			Mittelwert = MesseDistanz10()

		GPIO.cleanup()

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
