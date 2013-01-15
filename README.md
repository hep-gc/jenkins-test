#Overview
Python script used to boot a VM using repoman and monitor it using Jenkins.

##Usage
Running this script acts in a similar fashion as [vm-run](https://github.com/hep-gc/vm-helpers).
It will also pull any defaults you have saved in your vm-run config (`vm-run -C`).

###example
To run a virtual machine using sshpub key `~/.ssh/id_rsa.pub` with repoman image `image.in.repo.gz` on cloud `cloud1`.
```bash
./bootvm.py -s ~/.ssh/id_rsa.pub --repomanimage image.in.repo.gz -c cloud1
```
