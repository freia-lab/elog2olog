#!/bin/bash

while read  my_file
do
    d=`python getTaggedTxt.py $my_file -t isodate`
    t=`python getTaggedTxt.py $my_file -t time`
    echo $d $t $my_file
done



