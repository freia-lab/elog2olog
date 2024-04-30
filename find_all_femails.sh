#!/bin/bash

while read  my_file
do
     e=`python getTaggedTxt.py $my_file -t femail`
    
     echo $e
done


