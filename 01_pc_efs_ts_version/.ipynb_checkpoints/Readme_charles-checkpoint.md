# Instructions

- ssh ts-headnode via jump host
    - set up a .bat or .sh on windows laptop
    - your public key must be on both hosts both hops

```
$ cat ~/bin/ts-headnode
#! /bin/bash
bastion=ec2-user@10.12.71.52
headnode=ec2-user@172.16.6.67

ssh -J ${bastion} ${headnode}

```

# cd to application

```
cd /home/ec2-user/opt/timesync/01_efs_ts_version

```

# run the pc_user.py script

./pc_user.py --start_year 1984 --end_year 1984 lcnext_srs5000_final.csv

# validate_and_retry_failures_level_1

# validate_level_2

# xfer files to tallgrass using rsync