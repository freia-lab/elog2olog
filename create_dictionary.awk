BEGIN { print "dict = {" }
/uid:/||/userPassword:/ {
    if ($1=="uid:") {
	if (go==1) {
	    printf ",\n\t\"%s\": ",$2;
	} else {
	    printf "\t\"%s\": ",$2
	    go = 1;
	}
    }    
    else {
	if (go==1) printf "\"%s\"", $2;
    }
}
END { print "}" } 
