#!/bin/bash

while read  my_file
do
     s=`python getTaggedTxt.py $my_file -t severity`
     echo $s
done


