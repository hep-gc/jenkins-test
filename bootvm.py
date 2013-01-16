#!/usr/bin/python
import subprocess
import re
import sys
import time
import os

# Variables used for grabbing localpath and remote path from the arguments passed in when running the script
# Change these if defaults conflict with vm-run arguments
SHORT_LOCAL_PATH = '-lp'
LONG_LOCAL_PATH = '--localpath'
SHORT_REMOTE_PATH = '-rp'
LONG_REMOTE_PATH = '--remotepath'

# Simple usage print out if arguments were not properly input
USAGE = "\nScript Usage (not including vm-run arguments): \n\
        [{0} | {1}] - local path to file you want to copy onto created virtual machine. \n\
        [{2} | {3}] - path on virtual machine where the file (see -lp) will be copied to.".format(SHORT_LOCAL_PATH,LONG_LOCAL_PATH,SHORT_REMOTE_PATH,LONG_REMOTE_PATH)

        
# Check myproxy credentials. If error, exit, else credentials are valid.
def check_myproxy_logon():
    process = subprocess.Popen(["/usr/local/bin/repoman","whoami"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    process.wait()
    retcode = process.returncode
    out,err = process.communicate()
    if retcode != 0:
        raise Exception(out)

        
# Process the passed in arguments and creates vm-run command
def process_arguments():
    args = sys.argv[1:]
    localpath = ''
    remotepath = ''
    
    # If argument equals -lp, -rp, etc...save its value at index[n+1] and null index[n] and index[n+1] from the list to be filtered later.
    # If there is a syntax error in the arguments (-lp ) the exception will be raised.
    # If index goes out of bounds this indicates a syntax error in values passed to script.
    for n in range(0,len(args)):
        if args[n] == (SHORT_LOCAL_PATH or LONG_LOCAL_PATH):
            if not os.path.isfile(args[n+1]):
                raise IOError("File with path '{0}' does not exist.".format(args[n+1]))
            else:
                localpath = args[n+1]
                args[n] = args[n+1] = ''
        if args[n] == (SHORT_REMOTE_PATH or LONG_REMOTE_PATH):
            remotepath = args[n+1]
            args[n] = args[n+1] = ''
            
    # Filter the list to remove null entries.
    args = filter(None, args)

    # Create command for vm-run to boot machine given parametres passed in.
    cmd = ["/usr/local/bin/vm-run"] + args
    if not (remotepath and localpath):
        raise SyntaxError(USAGE)
    else:
        filename = os.path.basename(localpath)
        
    return cmd,localpath,remotepath,filename

    
# Boot VM if valid proxyuser and return hostname.
def boot_virtual_machine(cmd): 
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    process.wait()
    out,err = process.communicate()
    print out
    hostname = re.findall(r'Hostname = (.*?)\n', out)
    if not hostname:
        raise Exception("Hostname could not be resolved.")
    return hostname[0]

    
# If VM is launched ping the machine until its ready.
def virtual_machine_status(hostname):
    print "Virtual machine booting with hostname " + hostname + "... Please wait."
    process = subprocess.Popen(["ping","-c","1", hostname], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    retcode =  process.wait()
    while retcode != 0:
        process = subprocess.Popen(["ping","-n","1", hostname], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        process.wait()
        retcode =  process.poll()
        

# Then copy echo.py script onto newly created VM and run it.
def secure_copy_file(hostname,localpath,remotepath):
    print "Copying " + filename + " into " + remotepath + " on " + hostname
    cmd = "/usr/bin/scp " + localpath + " root@" + hostname + ":" + remotepath
    process =  subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    process.wait()
    retcode = process.returncode
    out,err = process.communicate()
    if retcode != 0:
        raise Exception(err)

        
# Run file on virtual machine we just booted and return its output.
def run_remote_file(hostname,remotepath,filename):
    cmd = "/usr/bin/ssh root@" + hostname + " " + remotepath + filename
    process =  subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    process.wait()
    retcode = process.returncode
    out,err = process.communicate()
    print out
    if retcode != 0:
        raise Exception(err)
    sanity_check(out)

    
# Check whether the hostname from vm-run and hostname returned from echo.py on the vm is the same.
def sanity_check(out):
    vmhostname = re.findall(r'Hostname: (.*?)\n', out)
    if vmhostname:
        vmhostname = vmhostname[0]
        if vmhostname == hostname:
            print "Both machine hostnames match!"
        else:
            raise Exception("Hostnames do not match.")
    else:
        raise Exception("Could not resolve virtual machine hostname from script output.")

# Where the magic happens.
def main():
    try:
        check_myproxy_logon()
        
        cmd,localpath,remotepath,filename = process_arguments()
        
        hostname = boot_virtual_machine(cmd)
        print "Virtual machine ready!"
        print "Waiting for SSH Server to become available..."
        time.sleep( 10 )
        
        virtual_machine_status(hostname)
        
        secure_copy_file(hostname,localpath,remotepath)
        
        run_remote_file(hostname,remotepath,filename)
        
        sys.exit(0)
    except IndexError as e:
        print USAGE
        sys.exit(1)
    except OSError as e:
        print "Error({0}): {1}. Is repoman AND vm-run installed?".format(e.errno,e.strerror)
        sys.exit(1)
    except Exception as e:
        print e
        sys.exit(1)
    

if __name__ == "__main__":
    main()
