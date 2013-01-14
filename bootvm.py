#!/usr/bin/python
import subprocess
import re
import sys
import time

if 'mchester' not in subprocess.Popen("/usr/local/bin/repoman whoami", shell=True, stdout=subprocess.PIPE).stdout.read():
	print "myproxy-logon expired. Quitting..."
	sys.exit()

print "Booting virtual machine..."
process = subprocess.Popen("/usr/local/bin/vm-run -s /var/lib/jenkins/.ssh/id_rsa.pub -i http://repoman.heprc.uvic.ca/api/images/raw/mchester/__hypervisor__/jenkins.gz",
			    shell=True, 
			    stdout=subprocess.PIPE, 
			    stderr=subprocess.PIPE)

for line in iter(process.stdout.readline, ""):
	print line
	if "Error:" in line:
		sys.exit()
	if "Hostname = " in line:
		hostname = re.findall(r'Hostname = (.*?)\n',line)[0]

if hostname is not '':
	print "Virtual machine booting with hostname: " + hostname 
	while '0 received' in subprocess.Popen("/bin/ping -c 1 -W 10 "+hostname, shell=True, stdout=subprocess.PIPE).stdout.read():
		time.sleep( 5 )
	print hostname + " is ready! You can now SSH into this virtual machine."
else:
	print "Hostname could not be resolved."

time.sleep( 10 )
print "Testing ssh"

cmd = "/usr/bin/scp /var/lib/jenkins/workspace/bootvm/echo.py root@" + hostname + ":/var/lib/jenkins/"
response =  subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.read()
print response

cmd = "/usr/bin/ssh root@" + hostname + " /var/lib/jenkins/echo.py"
response =  subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.read()
print response
