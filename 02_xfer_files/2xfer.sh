#! /bin/bash

#rs='rsync -avz -e ssh -- -J ec2-user@10.12.70.113' 

dest='butzer@tallgrass.cr.usgs.gov:/caldera/projects/usgs/water/impd/butzer/timesync/1984/'

srccsv='/efs/timesync/1984/'

#$rs $srccsv $dest

#rsync -azv -e 'ssh -J ec2-user@10.12.70.113' --exclude tc --exclude b743 --exclude b432 $srccsv $dest
#rsync -azv -e 'ssh -J ec2-user@10.12.70.113' --exclude tc --exclude b743 --exclude b432 $srccsv $dest


rsync -azv -e 'ssh -J ec2-user@10.12.70.113' $srccsv $dest



