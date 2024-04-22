#!/bin/bash

while read  my_file
do
    d=$(python getTaggedTxt.py $my_file -tstamp)
    echo $d $my_file
done

