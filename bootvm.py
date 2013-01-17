#!/usr/bin/env python

# Author: Mike Chester <mchester@uvic.ca>
# Copyright (C) 2013 University of Victoria
# You may distribute under the terms of either the GNU General Public
# License or the Apache v2 License.


import subprocess
import argparse
import time
import sys
import os
import re


# Variables used for grabbing localpath and remote path from the arguments passed in when running the script
# Change these if defaults conflict with vm-run arguments
SHORT_LOCAL_PATH = '-lp'
LONG_LOCAL_PATH = '--localpath'
SHORT_REMOTE_PATH = '-rp'
LONG_REMOTE_PATH = '--remotepath'

# Simple usage print out if arguments were not properly input
USAGE = "\nbootvm.py Usage (not including vm-run arguments): \n\
        [{0} | {1}] - local path to file you want to copy onto created virtual machine. \n\
        [{2} | {3}] - path on virtual machine where the file (see {0}) will be copied to.\n".format(SHORT_LOCAL_PATH,LONG_LOCAL_PATH,SHORT_REMOTE_PATH,LONG_REMOTE_PATH)

        
# Check myproxy credentials. 
def check_myproxy_logon():
    try:
        process = subprocess.Popen(["/usr/local/bin/repoman","whoami"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        process.wait()
        retcode = process.returncode
        out,err = process.communicate()

        # if repoman does not return 0 an error has occured.
        if retcode != 0:
            # we don't have valid credential
            # repoman will tell you what the problem is 
            print out
            sys.exit(retcode)
    
    # if repoman is not found exception will be caught here.
    except OSError as e:
        print "Error({0}): {1}. Is repoman installed?".format(e.errno,e.strerror)
        sys.exit(e.errno) 


# Process the passed in arguments and creates vm-run command
def process_arguments():

    # argparse is used here and will only work for python version 2.7+
    parser = argparse.ArgumentParser(description='bootvm help', usage=USAGE)
    parser.add_argument(SHORT_LOCAL_PATH,LONG_LOCAL_PATH, help="local path to file you want to copy.")
    parser.add_argument(SHORT_REMOTE_PATH,LONG_REMOTE_PATH, help="path on virtual machine where the file (see -{0}) will be copied to.".format(SHORT_LOCAL_PATH))

    bootvm_args,vmrun_args = parser.parse_known_args()

    localpath = bootvm_args.localpath
    remotepath = bootvm_args.remotepath

    # if an argument here is not known by vm-run, vm-run will handle the error.
    cmd = ["/usr/local/bin/vm-run"] + vmrun_args
   
    if not (remotepath and localpath):
        print parser.format_usage()
        sys.exit(1)
    else:
        filename = os.path.basename(localpath)

    return cmd,localpath,remotepath,filename

    
# Boot virtual machine and return hostname.
def boot_virtual_machine(cmd): 
    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        process.wait()

        retcode = process.returncode
        out,err = process.communicate()

        # if vm-run does not return 0 an error has occured.
        if retcode != 0:
            # vm-run will tell you the error
            print out
            sys.exit(retcode)

        hostname = re.findall(r'Hostname = (.*?)\n', out)
        
        print out

        if not hostname:
            print "Hostname could not be resolved."
            sys.exit(1)

        return hostname[0]

    # if vm-run is not found the exception will be caught here.
    except OSError as e:
        print "Error({0}): {1}. Is vm-run installed?".format(e.errno,e.strerror)
        sys.exit(e.errno)
    
# Pings the hostname until its ready.
def virtual_machine_status(hostname):
    try:
        print "Virtual machine booting with hostname {0}... Please wait.\n".format(hostname)

        process = subprocess.Popen(["ping","-c","1", hostname], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        process.wait()
        retcode = process.returncode

        # if ping does not receive any reply packets its return code is 1, indicating host is not accessible.
        # keep pinging until host become available.
        while retcode != 0:
            process = subprocess.Popen(["ping","-c","1", hostname], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            process.wait()
            retcode =  process.returncode

    # if ping is not found the exception will be caught here
    except OSError as e:
        print "Error({0}): {1}. ping not found.".format(e.errno,e.strerror)
        sys.exit(e.errno)

        
# Copy file onto hostname using scp.
def secure_copy_file(hostname,localpath,remotepath,filename):
    try:
        print "Copying {0} into {1} on {2}\n".format(filename,remotepath,hostname)

        # create scp command using localpath, hostname, and remotepath 
        cmd = "/usr/bin/scp {0} root@{1}:{2}".format(localpath,hostname,remotepath)

        process =  subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        process.wait()

        retcode = process.returncode
        out,err = process.communicate()
        
        # if scp does not return 0, an error occured.
        if retcode != 0:
            print err
            sys.exit(retcode)

    # if scp is not found exception will be caught here. 
    except OSError as e:
        print "Error({0}): {1}. scp not found.".format(e.errno,e.strerror)
        sys.exit(e.errno)

        
# Run file on hostname and return its output.
def run_remote_file(hostname,remotepath,filename):
    try:
        print "Running {0} on {1}\n\n".format(filename,hostname)

        cmd = "/usr/bin/ssh root@{0} {1}{2}".format(hostname,remotepath,filename)
        
        process =  subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        process.wait()

        retcode = process.returncode
        out,err = process.communicate()

        print "{0}OUTPUT OF {1}{0}\n".format("="*25,filename)
        print out

        # if ssh return code is not 0, an error occured. 
        if retcode != 0:
            print err
            sys.exit(retcode)
        
        # test the output of the ssh command with the hostname recovered from the vm-run command.
        sanity_check(hostname,out)

    # if ssh is not found the exception will be caught here.
    except OSError as e:
        print "Error({0}): {1}. ssh not found.".format(e.errno,e.strerror)
        sys.exit(e.errno)

    
# Check whether the hostname from vm-run and hostname returned from script on the virtual machine are the same.
def sanity_check(hostname,out):
    
    print "="*25 + "CHECKING HOSTNAMES" + "="*25 + "\n"
    vmhostname = re.findall(r'Hostname: (.*?)\n', out)

    # test vmhostname against the previous hostname, if they are not the same an error occured and will exit(1)
    # if hostname was not asked for in script (echo $hostname) then this will fail, but exit(0)
    if vmhostname:
        # since re.findall returns a list, grab first entry in list.
        vmhostname = vmhostname[0]
        print "Hostname: ",hostname
        print "Hostname returned: ", vmhostname

        if vmhostname == hostname:
            print "Both machine hostnames match!\n"
        else:
            print "Hostnames do not match. Something went wrong..."
            sys.exit(1)
    else:
        print "Hostname could not be recovered from output of script."
        sys.exit(0)


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
        
    except Exception as e:
        print "An unexpected error has occured.\n", e
        sys.exit(1)

if __name__ == "__main__":
    main()
