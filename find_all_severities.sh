#!/bin/bash

while read  my_file
do
#    t=`python test-tags.py $my_file`
#    a=`python getTaggedTxt.py $my_file -t author`
#    i=`python getTaggedTxt.py $my_file -t image`
#    f=`python getTaggedTxt.py $my_file -t file`
#    i=`python getTaggedTxt.py $my_file -t link`
     s=`python getTaggedTxt.py $my_file -t severity`
    
     echo $s
done


