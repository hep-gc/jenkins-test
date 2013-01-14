#!/usr/bin/python
import subprocess



out = subprocess.Popen("env", shell=True, stdout=subprocess.PIPE).stdout.read()
print "List of Enviroment Variables: " + out
out = subprocess.Popen("date", shell=True, stdout=subprocess.PIPE).stdout.read()
print "Current date: " + out
out = subprocess.Popen("echo $HOSTNAME", shell=True, stdout=subprocess.PIPE).stdout.read()
print "Hostname: " + out
