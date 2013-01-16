#!/usr/bin/python
import subprocess
import re
import sys
import time
import os

# Variables used for grabbing filepath and virtual machine filepath
# from the arguments passed in when running the script
# Change these if defaults conflict with vm-run arguments
_shortfilepath = '-fp'
_longfilepath = '-filepath'
_shortvmfilepath = '-vmfp'
_longvmfilepath = '-vmfilepath'

# Simple usage print out if arguments were not properly input
USAGE = "Script Usage (not including vm-run arguments): \n\
["+_shortfilepath+" | "+_longfilepath+"]     - path to file you want to copy onto created virtual machine. \n\
["+_shortvmfilepath+" | "+_longvmfilepath+"] - path on new virtual machine where the file (see -fp) will be copied to."

# Check myproxy credentials. If error, exit, else credentials are valid.
try:
    process = subprocess.Popen(["/usr/local/bin/repoman","whoami"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
except OSError:
    print 'Is repoman installed?',e
    sys.exit(1)
else:
    process.wait()
    retcode = process.returncode
    out,err = process.communicate()
    if retcode != 0:
        print out
        sys.exit(1)

# Grab arguments passed in from command line.
args = sys.argv[1:]

filepath = ''
vmpath = ''

# If argument equals -fp, vmfp, etc...save its value at index[n+1] and null index[n] and index[n+1] from the list to be filtered later.
# If there is a syntax error in the arguments (-fp ) the exception will be caught and program will exit.
for n in range(0,len(args)):
    try:
        if args[n] == (_shortfilepath or _longfilepath):
            if not os.path.isfile(args[n+1]):
                print "File +"+args[n+1]+" does not exist."
                sys.exit(1)
            else:
                filepath = args[n+1]
                args[n] = ''
                args[n+1] = ''
        if args[n] == (_shortvmfilepath or _longvmfilepath):
            vmpath = args[n+1]
            args[n] = ''
            args[n+1] = ''
    except Exception:
        print USAGE 
        sys.exit(1)

# Filter the list to remove null entries.
args = filter(None, args)

# Create command for vm-run to boot machine given parametres passed in.
cmd = ["/usr/local/bin/vm-run"] + args

## Boot VM if valid proxyuser.
#try:
#    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#    process.wait()
#    out,err = process.communicate()
#    print out
#except OSError:
#    print 'Is vm-run installed?', e
#    sys.exit(1)
#except CalledProcessError:
#    print out
#    sys.exit(1)
## If VM is launched, recover hostname from output, and ping the machine until its ready.
#hostname = re.findall(r'Hostname = (.*?)\n', out)
#if not hostname:
#    print "Hostname could not be resolved."
#    sys.exit(1)
#else:
#    hostname = hostname[0]
#    print "Virtual machine booting with hostname " + hostname + "... Please wait."
#    process = subprocess.Popen(["ping","-c","1", hostname], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#    process.wait()
#    retcode =  process.returncode
#    while retcode != 0:
#        process = subprocess.Popen(["ping","-c","1", hostname], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#        process.wait()
#        retcode =  process.returncode
#        time.sleep( 5 )
#    print "Virtual machine ready!"
#
## Wait 10 seconds for SSH server to become ready
## Then copy echo.py script onto newly created VM and run it.
#print "Waiting for SSH Agent to become available..."
#
#filepath = "/var/lib/jenkins/workspace/bootvm/echo.py"
#filename = os.path.basename(filepath)
#vmpath = "/var/lib/jenkins/"
#
#time.sleep( 10 )
#
## Copy file
#print "Copying " + filename + " into " + vmpath + " on " + hostname
#
#cmd = "/usr/bin/scp " + filepath + " root@" + hostname + ":" + vmpath
#process =  subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#process.wait()
#retcode = process.returncode
#out,err = process.communicate()
#print out
#if retcode != 0:
#    print err
#    sys.exit(retcode)
#
## Run file
#cmd = "/usr/bin/ssh root@" + hostname + " " + vmpath + filename
#process =  subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#process.wait()
#retcode = process.returncode
#out,err = process.communicate()
#print out
#if retcode != 0:
#    print err
#    sys.exit(retcode)
#
## Check whether the hostname from vm-run and hostname returned from echo.py on the vm is the same.
#vmhostname = re.findall(r'Hostname: (.*?)\n', out)
#if vmhostname:
#    vmhostname = vmhostname[0]
#    if vmhostname == hostname:
#        print "Both machine hostnames match!"
#        sys.exit()
#    else:
#        print "Hostnames do not match."
#        sys.exit(1)
