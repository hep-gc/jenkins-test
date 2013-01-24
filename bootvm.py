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

# cloud your booting VM on.
CLOUD = "Elephant"

# Simple usage print out if arguments were not properly input
USAGE = "\nbootvm.py Usage (not including vm-run arguments): \n\
        [{0} | {1}] - local path to file you want to copy onto created virtual machine. \n\
        [{2} | {3}] - path on virtual machine where the file (see {0}) will be copied to.\n".format(SHORT_LOCAL_PATH,LONG_LOCAL_PATH,SHORT_REMOTE_PATH,LONG_REMOTE_PATH)


# Timeout feature for subprocess.Popen - polls the process for timeout seconds waiting for it to complete
# If the process has exited return False (process did not timeout)
# Else if the process times out attempt to terminate the process or kill if terminate fails and return True (process timed out)
def check_popen_timeout(process, timeout=180):
    ret = True
    while timeout > 0:
        if process.poll() != None:
            ret = False
            break
        time.sleep(1)
        timeout -= 1
    if timeout == 0:
        print "subprocess timed out - attempting to terminate pid {0}".format(process.pid)
        try:
            process.terminate()
        except OSError as e:
            print "Error({0}): {1}.".format(e.errno,e.strerror)
            sys.exit(e.errno)
        time.sleep(2) # give OS a chance to terminate
        if process.poll() == None: # Did not terminate
            print "terminate() on pid {0} failed using kill()".format(process.pid)
            try:
                process.kill()
            except OSError as e:
                print "Error({0}): {1}.".format(e.errno,e.strerror)
                sys.exit(e.errno)
    return ret

# runs a shell command using Popen and will terminate the command if it takes longer than timeout to complete.
def run_command(cmd, timeout=180, use_shell=False):
    try:
        process = subprocess.Popen(cmd, shell=use_shell,  stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if check_popen_timeout(process,timeout):
            print "Command: '{0}' Timed out. Quitting...".format(cmd)
            sys.exit(1)
        process.wait()
        retcode = process.returncode
        out,err = process.communicate()
        return out,err,retcode
    except OSError as e:
        print "Error occured while running: '{0}'\nError({1}): {2} ".format(cmd,e.errno,e.strerror)
        sys.exit(e.errno)

# Process the passed in arguments and creates vm-run command
def process_arguments():
    # argparse is used here and will only work for python version 2.7+
    parser = argparse.ArgumentParser(description='bootvm help', usage=USAGE)
    parser.add_argument(SHORT_LOCAL_PATH,LONG_LOCAL_PATH, help="local path to file you want to copy.")
    parser.add_argument(SHORT_REMOTE_PATH,LONG_REMOTE_PATH, help="path on virtual machine where the file (see -{0}) will be copied to.".format(SHORT_LOCAL_PATH))

    file_args,vmrun_args = parser.parse_known_args()
    if not (file_args.localpath or file_args.remotepath):
        print parser.format_usage()
        sys.exit(1)
    return file_args,vmrun_args

# Check python version is > 2.6
def check_python_version():
    info = sys.version_info
    if info.major > 2 or (info.major > 1 and info.minor > 6):
        return
    else:
        print "Python version 2.7+ required.\nCurrent version: {0}.{1}.{2}".format(info.major,info.minor,info.micro)

# Check myproxy credentials.
def check_myproxy_logon():
    cmd = ["/usr/local/bin/repoman","whoami"]
    out,err,retcode = run_command(cmd)
    if retcode != 0:
        if (out or err):
            print out,err
        sys.exit(retcode)
    cmd = ["/cvmfs/grid.cern.ch/3.2.11-1/globus/bin/grid-proxy-info"]
    out,err,retcode = run_command(cmd)
    if retcode != 0:
        if (out or err):
            print out,err
        sys.exit(retcode)
    out = out.split('\n')
    temp = []
    for line in out:
        if 'timeleft' in line:
            temp = line.split(':')
    timeleft = int(temp[1])*60*60 + int(temp[2])*60 + int(temp[3])
    if timeleft < 300:
        print "Not enough time left on myproxy cert."
        sys.exit(1)

# Boot virtual machine and return hostname.
def boot_virtual_machine(vmrun_args):
    cmd = ["/usr/local/bin/vm-run"] + vmrun_args
    out,err,retcode = run_command(cmd,timeout=300)
    if retcode != 0:
        if (out or err):
            print out,err
        sys.exit(retcode)
    print out
    hostname = re.findall(r'Hostname = (.*?)\n', out)
    id = re.findall(r'Virtual Machine ID = (.*?)\n', out)
    if not (hostname and id):
        print "Could not resolve hostname or id."
        sys.exit(1)
    return id[0],hostname[0]

# Kill VM on specific cloud with ID returns true for success.
def kill_virtual_machine(id):
    id = "{0}-{1}".format(CLOUD,id)
    cmd = ["/usr/local/bin/vm-list","-c",CLOUD,"-k",id]
    out,err,retcode = run_command(cmd)
    if retcode != 0:
        if out or err:
            print out,err
        sys.exit(1)
    print out


# Pings the hostname until its ready.
def virtual_machine_status(hostname):
    print "Virtual machine booting with hostname {0}... Please wait.\n".format(hostname)
    cmd = ["ping","-c","1", hostname]

    out,err,retcode = run_command(cmd)
    # if ping does not receive any reply packets its return code is 1, indicating host is not accessible.
    # keep pinging until host become available.
    while retcode != 0:
        out,err,retcode = run_command(cmd)
        time.sleep( 1 )

# Copy file onto hostname using scp.
def secure_copy_file(hostname,file_args):
    localpath = file_args.localpath
    remotepath = file_args.remotepath
    filename = os.path.basename(localpath)

    print "Copying {0} into {1} on {2}\n".format(filename,remotepath,hostname)
    # create scp command.
    cmd = ["/usr/bin/scp","-o","StrictHostKeyChecking=false",localpath,"root@{0}:{1}".format(hostname,remotepath)]
    out,err,retcode = run_command(cmd)
    if retcode != 0:
       if (out or err):
           print out,err
       sys.exit(retcode)

# Run file on hostname and return its output.
def run_remote_file(hostname,file_args):
    filename = os.path.basename(file_args.localpath)
    filepath = os.path.join(file_args.remotepath,filename)

        # create ssh command
    cmd = ["/usr/bin/ssh","-o","StrictHostKeyChecking=false","root@{0}".format(hostname),filepath]
    out,err,retcode = run_command(cmd)
    if retcode != 0:
       if (out or err):
           print out,err
       sys.exit(retcode)
    print "{0}OUTPUT OF {1}{0}\n".format("="*25,filename)
    return out

# Check whether the hostname from vm-run and hostname returned from script on the virtual machine are the same.
def sanity_check(hostname,out):
    print "{0}CHECKING HOSTNAMES{0}\n".format("="*25)
    vmhostname = re.findall(r'Hostname: (.*?)\n', out)
    # test vmhostname against the previous hostname, if they are not the same an error occured and will exit(1)
    # if hostname was not asked for in script (echo $hostname) then this will fail, but exit(0)
    if vmhostname:
        print "Hostname: ",hostname
        print "Hostname returned: ", vmhostname[0]
        if vmhostname[0] == hostname:
            print "Both machine hostnames match!\n"
        else:
            print "Hostnames do not match. Something went wrong..."
    else:
        print "Hostname could not be recovered from output of script."

def main():
    try:
        check_python_version()
        check_myproxy_logon()

        file_args,vmrun_args= process_arguments()

        id,hostname = boot_virtual_machine(vmrun_args)

        virtual_machine_status(hostname)

        print "Waiting for SSH Server to become available...\n"
        time.sleep( 3 )

        secure_copy_file(hostname,file_args)

        output = run_remote_file(hostname,file_args)
        print output

        sanity_check(hostname,output)

        print "Attempting to shutdown virtual machine..."
        kill_virtual_machine(id)

    except Exception as e:
        print "An unexpected error has occured.\n", e
        sys.exit(1)

if __name__ == "__main__":
    main()
