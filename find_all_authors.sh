#!/bin/bash

while read  my_file
do
     a=`python getTaggedTxt.py $my_file -t author`
     echo $a
done


