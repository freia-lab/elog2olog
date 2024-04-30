#!/bin/bash

while read  my_file
do
    c=`python getTaggedTxt.py $my_file -t category`
    
     echo $c
done


