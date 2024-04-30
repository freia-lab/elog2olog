#!/bin/bash

while read  my_file
do
    k=`python getTaggedTxt.py $my_file -t keywords`
    
    echo $k
done


