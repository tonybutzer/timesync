#! /bin/bash

rs='rsync -avz -e ssh -J ec2-user@10.12.70.113' 
dest='butzer@tallgrass.cr.usgs.gov:/caldera/projects/usgs/water/impd/butzer/timesync/'

srccsv='/efs/timesync/1984/*.csv'

$rs $srccsv $dest

