#Overview
Python script used to boot a virtual machine using **[repoman](https://github.com/hep-gc/repoman)** / **[vm-run](https://github.com/hep-gc/vm-helpers)**, it will then copy a user defined script into a user defined directory on the created virtual machine and run it, which can then be monitored by **[jenkins](http://jenkins-ci.org/)**.

Works for Python 2.6+.

##Usage
Running this script acts in a similar fashion as **[vm-run](https://github.com/hep-gc/vm-helpers)**.
It also features two additional parametres for copying a local file onto the newly booted virtual machine:
```
[-lp | --localpath]  - local path to file you want to copy onto created virtual machine.
[-rp | --remotepath] - path on virtual machine where the file (see -lp) will be copied to.
```
_These shortcuts can be changed easily in the script if there is an issue._

This script will also pull any defaults you have saved in your vm-run config (`vm-run -C`).

###Example Command
To create a virtual machine using repoman image `image.gz` with sshpub key `~/.ssh/id_rsa.pub` and run `echo.py` from the remote directory `/home/temp/` on the created virtual machine.
```bash
$./bootvm.py -s ~/.ssh/id_rsa.pub -R image.gz -lp /path/to/echo.py -rp /home/temp/
```
