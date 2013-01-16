#!/usr/bin/python
import subprocess
import re
import sys
import time
import os
import argparse

# Variables used for grabbing localpath and remote path from the arguments passed in when running the script
# Change these if defaults conflict with vm-run arguments
SHORT_LOCAL_PATH = '-lp'
LONG_LOCAL_PATH = '--localpath'
SHORT_REMOTE_PATH = '-rp'
LONG_REMOTE_PATH = '--remotepath'

# Simple usage print out if arguments were not properly input
USAGE = "\nScript Usage (not including vm-run arguments): \n\
        [{0} | {1}] - local path to file you want to copy onto created virtual machine. \n\
        [{2} | {3}] - path on virtual machine where the file (see {0}) will be copied to.\n".format(SHORT_LOCAL_PATH,LONG_LOCAL_PATH,SHORT_REMOTE_PATH,LONG_REMOTE_PATH)

        
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
    parser = argparse.ArgumentParser(description='bootvm help')

    parser.add_argument(SHORT_LOCAL_PATH,LONG_LOCAL_PATH, help="local path to file you want to copy.")
    parser.add_argument(SHORT_REMOTE_PATH,LONG_REMOTE_PATH, help="path on virtual machine where the file (see -"+SHORT_LOCAL_PATH+") will be copied to.")
    
    args = parser.parse_known_args()
    localpath = args[0].localpath
    remotepath = args[0].remotepath
    cmd = ["/usr/local/bin/vm-run"] + args[1]
   
    # If remotepath or localpath are null this will raise a syntax error and print the USAGE statement.
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
    print "Virtual machine booting with hostname " + hostname + "... Please wait.\n"
    process = subprocess.Popen(["ping","-c","1", hostname], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    process.wait()
    retcode = process.returncode
    while retcode != 0:
        process = subprocess.Popen(["ping","-c","1", hostname], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        process.wait()
        retcode =  process.returncode
        

# Then copy echo.py script onto newly created VM and run it.
def secure_copy_file(hostname,localpath,remotepath,filename):
    print "Copying " + filename + " into " + remotepath + " on " + hostname + "\n"
    cmd = "/usr/bin/scp " + localpath + " root@" + hostname + ":" + remotepath
    process =  subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    process.wait()
    retcode = process.returncode
    out,err = process.communicate()
    if retcode != 0:
        raise Exception(err)

        
# Run file on virtual machine we just booted and return its output.
def run_remote_file(hostname,remotepath,filename):
    print "Running " + filename + " on " + hostname + "\n\n"
    cmd = "/usr/bin/ssh root@" + hostname + " " + remotepath + filename
    process =  subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    process.wait()
    retcode = process.returncode
    out,err = process.communicate()
    print "="*25 + "OUTPUT OF " + filename + "="*25 + "\n"
    print out
    if retcode != 0:
        raise Exception(err)
    sanity_check(hostname,out)

    
# Check whether the hostname from vm-run and hostname returned from echo.py on the vm is the same.
def sanity_check(hostname,out):
    print "="*25 + "CHECKING HOSTNAMES" + "="*25 + "\n"
    vmhostname = re.findall(r'Hostname: (.*?)\n', out)
    if vmhostname:
        vmhostname = vmhostname[0]
        print "Hostname: ",hostname
        print "Hostname returned: ", vmhostname
        if vmhostname == hostname:
            print "Both machine hostnames match!\n"
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
        print "Virtual machine ready!\n"

        virtual_machine_status(hostname)
        print "Waiting for SSH Server to become available...\n"
        time.sleep( 10 )
        
        secure_copy_file(hostname,localpath,remotepath,filename)
        
        run_remote_file(hostname,remotepath,filename)
        
    except IndexError as e:
        print USAGE
        sys.exit(1)
    except OSError as e:
        print "Error({0}): {1}. Is repoman AND vm-run installed?".format(e.errno,e.strerror)
        sys.exit(e.errno)
    except Exception as e:
        print e
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
