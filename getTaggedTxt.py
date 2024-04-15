import sys
import os
import re
import mimetypes
from datetime import datetime, timezone, timedelta

import wikitextparser as wtp
from bs4 import BeautifulSoup

def datetime_to_unix_milliseconds(date_str, time_str):
    # Parse date and time strings into datetime object
    date_obj = datetime.strptime(date_str + ' ' + time_str, '%Y-%m-%d %H:%M:%S')
    
    # Convert datetime object to Unix timestamp in seconds
    unix_timestamp = date_obj.replace(tzinfo=timezone.utc).timestamp()
    
    # Convert Unix timestamp to milliseconds
    unix_milliseconds = int(unix_timestamp * 1000)
    
    return unix_milliseconds

def get_mime_type(file_name):
    mime_type, _ = mimetypes.guess_type(file_name)
    return mime_type

def parse_path(path):
    directory, filename = os.path.split(path)
    return directory, filename

def extract_content_between_tags(input_string, tag):
    pattern = fr"<{tag}>(.*?)</{tag}>"
    matches = re.findall(pattern, input_string, re.DOTALL)
    if matches:
        return matches[0]
    else:
        return "None"

def parse_wiki_markup(text):
    parsed = wtp.parse(text)
    print(parsed.sections)

def wiki2commonmark(input_data):
    commonmark0 = input_data.replace("\n", "  \n")
    return commonmark0

def get_tagged(soup, tag):
    value = soup.find(tag)
#    print(value)
    if (tag == "title"):
        if len(value.contents) == 0:
            return "None"
        else:
            return soup.find(tag).contents[0]
    if (tag == "femail"):
        if len(value.contents) == 0:
            return "None"
        else:
            return soup.find(tag).contents[0]
  
    return soup.find(tag).contents[0]

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 program.py <file_path> [-t <tag>] [-l <logbook>]")
        return

    file_path = sys.argv[1]
    directory, filename = parse_path(file_path)

    # Open the document and create a soup object
    with open(file_path, 'r') as fp:
        data = fp.read()
    soup = BeautifulSoup(data, 'html.parser')
#    for t in soup.find_all(True):
#        print(t.name)
#    print (soup)
    # Default values for tag and logbook
    tag = None
    logbook = None

    # Check for optional arguments
    i = 2  # Start index for optional arguments
    while i < len(sys.argv):
        if sys.argv[i] == '-t':
            if i + 1 < len(sys.argv):
                tag = sys.argv[i + 1]
                i += 2  # Skip tag value
            else:
                print("Error: -t flag requires a tag value.")
                return
        elif sys.argv[i] == '-l':
            if i + 1 < len(sys.argv):
                logbook = sys.argv[i + 1]
                i += 2  # Skip logbook value
            else:
                print("Error: -l flag requires a logbook value.")
                return
        else:
            print("Error: Invalid option", sys.argv[i])
            return

        #    print("Directory:", directory)
        #    print("File Name:", filename)
    try:
        if tag == "image":
            fname = extract_content_between_tags(data, tag)
            if fname != "None":
                attachment = directory + "/" + extract_content_between_tags(data, "link")
                # print ("Attachment: "+fname+"  \t\t\t"+attachment+" ("+get_mime_type(attachment)+")")
                print('Attachment: {0!s:.<40}{1!s:.<60s}{2}'.format(fname, attachment, get_mime_type(attachment)))
        else:
            #print("Tag:", tag, "value: ", get_tagged(soup, tag))
            content = get_tagged(soup, tag)
            # convert from wiki markup to commonmark 
#            print(content.replace("\n", "  \n"))
            #print (dir(content))
            if (tag == "text"):
                # convert from wiki markup to commonmark 
                commonmark = wiki2commonmark (content)
                print (commonmark)
                parse_wiki_markup(str(commonmark))
                
        #print("Logbook:", logbook)
    except Exception as e:
        print(f"Error in {file_path}: {str(e)}")

if __name__ == "__main__":
    main()
