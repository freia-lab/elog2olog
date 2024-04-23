#!/bin/bash
# Usage: migrate_directory {<directory-to migrate> | <file-name-containing-log-entry-file-names>}"<arguments to migrateElog2Olog.py after log file name>

BLACK=$(tput setaf 0)
RED=$(tput setaf 1)
GREEN=$(tput setaf 2)
YELLOW=$(tput setaf 3)
LIME_YELLOW=$(tput setaf 190)
POWDER_BLUE=$(tput setaf 153)
BLUE=$(tput setaf 4)
MAGENTA=$(tput setaf 5)
CYAN=$(tput setaf 6)
WHITE=$(tput setaf 7)
BRIGHT=$(tput bold)
NORMAL=$(tput sgr0)
BLINK=$(tput blink)
REVERSE=$(tput smso)
UNDERLINE=$(tput smul)

DIR=$1
ARGS=$2
TEMPL=$(echo "$DIR" | sed 's/\//_/g')
if [ -d $DIR ]; then
    TMPFILE=$(mktemp $TEMPL-XXX)
    n=$(find $DIR -name "20*xml" | wc -l)
    sec=$(echo "0.11 * $n" | bc)
    echo Sorting the log entries according to isodate and time tags - it will take about $(printf "%.0f" "$sec") seconds...
    echo $(date)
    find $DIR -name "20*xml" | ./get_timestamps.sh | sort | awk '{print $3}' | tee $TMPFILE > /dev/null
    echo $(date)
else
    TMPFILE=$DIR
    n=$(wc -l $TMPFILE)
fi

echo Using $TMPFILE
#cat $TMPFILE

i=1
while read -r my_file
do
    echo -n "Processing $my_file ($i/$n)... "
    out=$(python migrateElog2Olog.py $my_file $ARGS)
    ((i++))
    if [[ "$out" == "OK" ]]; then
	echo ${GREEN}$out${NORMAL}
    else
	if [[ "$out" == "DELETED" ]]; then
	    echo ${BLUE}$out${NORMAL}
	else
	    echo ${RED}$out${NORMAL}
	fi
    fi
done < "$TMPFILE"

#rm $TMPFILE
