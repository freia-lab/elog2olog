#!/bin/bash

while read  my_file
do
    t=`python getTaggedTxt.py $my_file -t title`
    a=`python getTaggedTxt.py $my_file -t author`
    i=`python getTaggedTxt.py $my_file -t image`
    s=`python getTaggedTxt.py $my_file -t severity`
    k=`python getTaggedTxt.py $my_file -t keywords`
    x=`python getTaggedTxt.py $my_file -t text`
#    f=`python getTaggedTxt.py $my_file -t file`
#    i=`python getTaggedTxt.py $my_file -t link`
#     echo $a $t
    echo $a
    echo $t
    echo $s
    echo $k
    echo $x
    if [ ! -z "$i" ]
    then
	echo  $i
    fi
done



