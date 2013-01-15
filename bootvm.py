#!/usr/bin/python
import subprocess
import re
import sys
import time
import os

#Check myproxy credentials. If error, exit, else credentials are valid.
process = subprocess.Popen(["/usr/local/bin/repoman","whoami"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
process.wait()
retcode = process.returncode
out,err = process.communicate()
if retcode != 0:
    sys.exit(retcode)

arg = sys.argv[1:]
cmd = ["/usr/local/bin/vm-run"] + arg

#Boot VM if valid proxyuser.
process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
process.wait()
out,err = process.communicate()
print out
if "Error:" in out:
    sys.exit(retcode)

#If VM is launched, recover hostname from output, and ping the machine until its ready.
hostname = re.findall(r'Hostname = (.*?)\n', out)
if not hostname:
    print "Hostname could not be resolved."
    sys.exit(1)
else:
    hostname = hostname[0]
    print "Virtual machine booting with hostname " + hostname + "... Please wait."
    process = subprocess.Popen(["ping","-c","1", hostname], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    process.wait()
    retcode =  process.returncode
    while retcode != 0:
        process = subprocess.Popen(["ping","-c","1", hostname], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        process.wait()
        retcode =  process.returncode
        time.sleep( 5 )
    print "Virtual machine ready!"

#Wait 10 seconds for SSH agent to become ready
#Then copy echo.py script onto newly created VM and run it.
print "Waiting for SSH Agent to become available..."

filepath = "/var/lib/jenkins/workspace/bootvm/echo.py"
filename = os.path.basename(filepath)
vmpath = "/var/lib/jenkins/"

time.sleep( 10 )

#copy file
print "Copying " + filename + " into " + vmpath + " on " + hostname

cmd = "/usr/bin/scp " + filepath + " root@" + hostname + ":" + vmpath
process =  subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
process.wait()
retcode = process.returncode
out,err = process.communicate()
print out
if retcode != 0:
    print err
    sys.exit(retcode)

#run file
cmd = "/usr/bin/ssh root@" + hostname + " " + vmpath + filename
process =  subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
process.wait()
retcode = process.returncode
out,err = process.communicate()
print out
if retcode != 0:
    print err
    sys.exit(retcode)

#Check whether the hostname from vm-run and hostname returned from echo.py on the vm is the same.
vmhostname = re.findall(r'Hostname: (.*?)\n', out)
if vmhostname:
    vmhostname = vmhostname[0]
    if vmhostname == hostname:
        print "Both machine hostnames match!"
        sys.exit()
    else:
        print "Hostnames do not match."
        sys.exit(1)
