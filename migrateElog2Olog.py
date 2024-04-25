import sys
import os
import re
import mimetypes
import math
from datetime import datetime, timezone, timedelta
import requests
import json
import uuid
import pytz
from past.builtins import execfile

from requests_toolbelt.multipart.encoder import MultipartEncoder

from requests.auth import HTTPBasicAuth
from PIL import Image

import wikitextparser as wtp
from bs4 import BeautifulSoup
import html

EMBEDED_IMAGE_WIDTH = 800

execfile('passwds.py')

def get_image_size(file_path):
    try:
        with Image.open(file_path) as img:
            width, height = img.size
            return width, height
    except IOError:
        #print(f"Unable to open image file: {file_path}")
        return None

def datetime_to_unix_milliseconds(date_str, time_str):
    # Parse date and time strings into datetime object
    date_obj = datetime.strptime(date_str + ' ' + time_str, '%Y-%m-%d %H:%M:%S')

    # Create a timezone object for CEST
    cest = pytz.timezone('Europe/Stockholm')

    # Localize the datetime object to CEST timezone
    localized_date = cest.localize(date_obj)

    # Convert localized datetime object to Unix timestamp in milliseconds
    unix_milliseconds = int(localized_date.timestamp() * 1000)

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
        return None
    
def replace_tags(input_string, str1, str2, str3, str4):
    # Find the start index of str1 in the input string
    start_index = input_string.find(str1)
    #print (">>>>>>>>>>>>>Input string to replace_tags: ",input_string)
    if start_index != -1:
        # Find the end index of str2 after str1
        end_index = input_string.find(str2, start_index + len(str1))
        
        if end_index != -1:
            # Calculate the length of the string between str1 and str2 together with str1 and str2
            text_length = end_index - start_index  + len(str2)
            
            # Replace str1 with str3 and str2 with str4
            replaced_string = str3 + input_string[start_index + len(str1):end_index] + str4
           
            return start_index, text_length, replaced_string

    return -1, 0, input_string

    
def format_italic_bold (input_string, str1, str2):
    commonmark = ""
    main_index = 0
    input_data_length = len(input_string)
    while main_index < input_data_length:
        #print("DEBUG: main_index: ", main_index)
        indx, length, block = replace_tags(input_string[main_index:], str1, str1, str2, str2)
        #print ("DEBUG: block_length, indx, block: " ,length, indx, block)
        if (indx >= 0):
            if block.count("\n")>0:
                main_indx = main_indx + len(str1)
                continue
            commonmark = commonmark + input_string[main_index:main_index+indx]
            commonmark = commonmark + block
            main_index = main_index + length + indx
        else:
            commonmark = commonmark + input_string[main_index:]
            break
    return commonmark

def find_url(input_string):
    pattern = r'\b(?:https?://)\S+(?=\s|\)|\.)'
    # Add \n to the end to prevent error when there is no
    # terminating chracter in input_string and the url
    # is the last entry in the input
    match = re.search(pattern, input_string+"\n")
    if match:
        url = match.group(0)
        start_index = match.start()
        # Find the last character of the URL
        end_index = start_index + len(url) - 1
        if input_string[end_index] in (' ', ')', '.'):
            url = url[:-1]  # Exclude the trailing character
        return url, start_index
    else:
        return None, -1

def format_url_links(input_string):
    main_index = 0
    output_string = ""
    url = ""
    while url != None:
        url, indx = find_url(input_string[main_index:])
        #print("DEBUG(format_url_links): url: ", url)
        if url:
            commonmark_link = url.replace(url, "["+url+"]("+url+")")
            output_string += input_string[main_index:main_index+indx] + commonmark_link
            main_index += indx + len(url)
        else:
            output_string += input_string[main_index:]  
    return output_string
                    
    
# Format the tables (add a second row as a separator and \n before the title bar)
def format_tables(input_data):
    output_data = ""
    main_index = 0
    # Add a neline in the beginning to have the same find string even for the first line
    input_data = "\n" + input_data
    input_data_length = len(input_data)
    #print ("DEBUG (format_tables): input_data_length:"+str(input_data_length)+" data: \n"+input_data)
    while main_index < input_data_length:
        indx = input_data.find("\n|", main_index)
        #print ("DEBUG(format_tables):  main_ind: ", main_index)
        if (indx < 0):
            output_data = output_data + input_data[main_index:]
            #print ("DEBUG(format_tables): no more tables")
            break
        else:
            output_data += input_data[main_index:indx]
            #print ("DEBUG(format_tables): text b4 the table: indx: "+str(indx)+" output_data: \n"+output_data)
            main_index = indx
            eol_indx = input_data.find("\n", main_index+1)
            columns = input_data.count("|",main_index,eol_indx)
            title_line =  input_data[main_index:eol_indx]
            last_bar_indx = main_index
            n = columns
            while last_bar_indx != -1 and n > 0:
                last_bar_indx = input_data.find("|", last_bar_indx+1)
                #print("DEBUG(format_tables): n, last_bar_indx: ", n, last_bar_indx)
                n -= 1
            #print("DEBUG(format_tables): textefter last bar ", input_data[last_bar_indx+1:eol_indx])  
            if input_data[last_bar_indx+1:eol_indx].isspace():
                columns -= 1
            #print("DEBUG(format_tables): title line: ", input_data[main_index:eol_indx])
            #print("DEBUG(format_tables): found columns: ", columns)
            # copy the first row (title with the terminating \n) and add leading \n
            output_data += "\n" + input_data[main_index:eol_indx+1]
            #print ("DEBUG(format_tables): output_data: ", output_data)
            # Insert the separator between the title and the contents
            main_index = eol_indx
            for i in range(columns):
                output_data += "|-"
            #output_data += "\n"
            #print("DEBUG(format_table): Separator line: ", output_data[main_index:])
            # copy rest of the table
            while input_data.find("\n|", main_index) >= 0:
                line = input_data[main_index:input_data.find("\n", main_index+1)]
                output_data += line
                main_index += len (line)
    #print("DEBUG (format_tables): output_data: ", output_data)
    return output_data
    
# Change the wiki formatting to commonmark (text outside the code block)
def replace_formatting(input_data):
    # replace the numbered list formatting
    #print("DEBUG(replace_fromatting): input_data: ", input_data)
    output_data = input_data.replace("\n#", "\n1. ")
    # Replace the nested lists (first the third level, then the second
    output_data = output_data.replace("\n  *", "\n    *")
    output_data = output_data.replace("\n *", "\n  *")
    # Replace the headings
    output_data = output_data.replace("\n!!", "\n# ")
    output_data = output_data.replace("\n!", "\n## ")
    output_data = format_italic_bold (output_data, "``", "*")
    output_data = format_italic_bold (output_data, "_`", "***")
    output_data = format_tables (output_data)
    output_data = format_url_links (output_data)
    return output_data

def wiki2commonmark(input_data):
    # Add 2 spaces before <newline> to make a line breake
    if input_data is not None:
        commonmark0 = input_data.replace("\n", "  \n")
    else:
        return ""
    commonmark=""
    main_index = 0
    input_data_length = len(commonmark0)
    if debug > 1:
        print ("DEBUG(wiki2commonmark): inp_data_length: " ,input_data_length)
    while main_index < input_data_length:
        if debug > 1:
            print("DEBUG(wiki2commonmark): main_index: "+str(main_index)+"   Data@main_index: "+commonmark0[main_index:main_index+40])
        # Insert <newline> as the first character in order to make the search for tags
        # the same in the beginiing of the document as in hte rest of it
        indx, length, block = replace_tags("\n"+commonmark0[main_index:], "\n{{", "\n}}  \n", "\n```\n", "\n```\n")
        if debug > 1:
            print ("DEBUG(wiki2commonmark): block_length, indx: " ,length, indx)
        if (indx >= 0):
            commonmark = commonmark + replace_formatting(commonmark0[main_index:main_index+indx])
            commonmark = commonmark + block
            main_index = main_index + length + indx - 1
            if debug > 1:
                print("DEBUG(wiki2commonmark): main_index after the last code block:", main_index)
        else:
            commonmark = commonmark + replace_formatting(commonmark0[main_index:])
            break
    return commonmark

def get_tagged(soup, tag):
    value = soup.find(tag)
    if tag == "title":
        start_indx = soup.find("<"+tag+">")+len(tag)+2
        stop_indx = soup.find("</"+tag+">")
        if (start_indx < 0) or (len(soup[start_indx:stop_indx])) == 0:
            return None
        else:
            print ("Title: ",soup[start_indx:stop_indx], "  start: ", start_indx, "  end: ", stop_indx)
            return soup[start_indx:stop_indx]
        
    if len(value.contents) == 0:
        return None
    else:
        return soup.find(tag).contents[0]

def get_owner(data):
    knownAuthors = ("KG","KF","RSK","AM","CS","CW","EP","IP","JE","KP","LH",
                    "MZ","RSK","SE","TB","TP")
    guest = "guest"
    a = extract_content_between_tags(data, "author")
    for i in (3,2):
        if a[0:i].upper() in knownAuthors:
            if len(a) == i:
                return a.upper(), ""
            if len(a) > i:
                return knownAuthors[knownAuthors.index(a[0:i].upper())], "Author(s): "+a+"  \n"
    if len(a) == 0:
        return guest, "Author unknown  \n"
    return guest,"Author(s): "+a+"  \n"
 
def get_title(data):
    t = extract_content_between_tags(data, "title")
    if t is None:
        return "Untitled"
    if t == "":
        return "Untitled"
    return html.unescape(t)

def get_tag(data):
    k = extract_content_between_tags(data, "keywords")
    match k:
        case "not set":
            return ""
        case "System":
            return "Control system"
        case "CM":
            return "Cryomodule"
    return k

def get_level(data):
    l = extract_content_between_tags(data, "severity")
    if (l == "NONE"):
        l = "Normal"
    return l

def get_server_info(api_endpoint):
    info = None
    try:
        response = requests.get(api_endpoint)
        if response.status_code == 200:
            info = response.text
        else:
            print(f"Failed to get server info. Status code: {response.status_code}")
    except Exception as e:
        print("An error occurred: ",{str(e)})
    return info
    
def create_log_entry_with_attachments(api_endpoint, logbook, owner, authors, timestamp, title, level, tags, descr, attachment, dry_run):
    # Ignore empty entries
    if (descr == "") and (title == "Untitled"):
        return "EMPTY"
    # Get server info
    maxFileSize = 15
    maxRequestSize = 50
    tag_entry = ""
    serverInfo = get_server_info(api_endpoint)
    if debug > 1:
        print ("Server info: ", get_server_info(api_endpoint))
    if serverInfo is not None:
        info = json.loads(get_server_info(api_endpoint))
        serverConfig = info["serverConfig"]
        maxFileSize = info["serverConfig"]["maxFileSize"]
    
    # Prepare log entry payload

    if tags != "":
        tag_entry = [tags]
    else:
        tag_entry = []
    attchmntId = str(uuid.uuid4())
    if (attachment[0] == None):
        log_entry = {
            "description": authors+descr,
            "level": level,
            "title": title,
            "logbooks": [{"name": logbook}],
            "tags": tag_entry,
            "events": [{"name":"OriginalCreatedDate","instant": timestamp }]
        }
    else:
        scale = ""
        embedded = ""
        if os.path.getsize(attachment[1]) > maxFileSize * 1000000:
            return ("Attachment file too big (max size: {0}MB)".format(maxFileSize))
        if (attachment[2] is not None) and (attachment[2].find("image") == 0):
            width, height = get_image_size(attachment[1])
            if debug > 1:
                print("DEBUG(create_log_entry_with_attachments): image size {0}x{1}".format(width, height))
            if width > EMBEDED_IMAGE_WIDTH:
                scale = 'width={0:d} height={1:d}'.format(EMBEDED_IMAGE_WIDTH, math.trunc(height*EMBEDED_IMAGE_WIDTH/width))
                scale = "{"+scale+"}"
            embedded = "![](attachment/"+attchmntId+")"+scale
        if debug > 1:
            print("DEBUG(create_log_entry_with_attachments): Scale: ", scale)
        log_entry = {
            "description": authors+descr+"\n\nSee attachment  \n"+embedded,
            "level": level,
            "title": title,
            "logbooks": [{"name": logbook}],
            "tags": tag_entry,
            "events": [{"name":"OriginalCreatedDate","instant": timestamp }],
            "attachments":[
            {"id": attchmntId, "filename": attachment[0]}
            ]
        }
        if debug > 1:
            print ("DEBUG(attachment(create_log_entry_with_attachments): attachment: ", attachment)

    # Prepare the log entry payload as JSON
    if debug > 1:
        print ("DEBUG(attachment(create_log_entry_with_attachments): log_entry: ", log_entry)
    json_data = json.dumps(log_entry)
    # Prepare the multipart encoder
    if (attachment[0] == None):
        multipart_data = MultipartEncoder(
            fields={
                'logEntry': ('logEntry.json', json_data, 'application/json')
            }
        )
    else:
        multipart_data = MultipartEncoder(
            fields={
                'logEntry': ('logEntry.json', json_data, 'application/json'),
                'files': (attachment[0], open(attachment[1], 'rb'), attachment[2])
            }
        )
    
    # Set the Content-Type header with the boundary
    headers = {
        'Content-Type': multipart_data.content_type
    }
    if debug > 1:
        print("DEBUG(create_log_entry_with_attachments): Content-Type " + multipart_data.content_type)
        print("DEBUG(create_log_entry_with_attachments): multipart_data: ", multipart_data)
    api_endpoint += "/logs/multipart"
    try:
        if not dry_run:
            response = requests.put(api_endpoint, headers=headers, data=multipart_data, auth=HTTPBasicAuth(owner, dict[owner]))
        else:
            return "OK"
        if response.status_code == 200:
            return "OK"
        else:
            return "Failed to create log entry. Status code: {0}".format(response.status_code)
    except Exception as e:
        return "An error occurred: " + str(e)
    return "OK"

def main():
    attachment = [None,None,None]
    debug = 0
    dry_run = False
     # Default values for url and logbook
    url = "https://freia-olog.physics.uu.se:8181/Olog"
    logbook = "test"
   
    if len(sys.argv) < 2:
        print("Usage: python3 migrateElog2Olog.py <file_path> [-l <logbook>] [-u <url>] [-d] [-n]")
        return

    file_path = sys.argv[1]
    directory, filename = parse_path(file_path)

    # Open the document and create a soup object
    with open(file_path, 'r') as fp:
        data = fp.read()
    soup = BeautifulSoup(data, 'html.parser')
#    print (soup)

    # Check for optional arguments
    i = 2  # Start index for optional arguments
    while i < len(sys.argv):
        if sys.argv[i] == '-u':
            if i + 1 < len(sys.argv):
                url = sys.argv[i + 1]
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
        elif sys.argv[i] == '-d':
            debug = 1
            i += 1
        elif sys.argv[i] == '-n':
            dry_run = True
            i += 1
        else:
            print("Error: Invalid option", sys.argv[i])
            return

        #print("Directory:", directory)
        #print("File Name:", filename)
    #try:
    owner, authors = get_owner(data)
    title = get_title(data)
    level = get_level(data)
    if level == "DELETE":
        print("DELETED")
        return
    tags = get_tag(data)
    d =  extract_content_between_tags(data, "isodate")
    t = extract_content_between_tags(data, "time")
    if len(t) == 5:
        t = t + ":00"
    timestamp = datetime_to_unix_milliseconds(d,t)
    if debug > 0:
        print('Logbook: {6}\nAuthor: {1} ({5})\tTitle: {0}\nLevel: {2!s:.<20s}Keyword: {3!s:.<20s}Timestamp: {4}'.format(title,owner,level,tags,timestamp, authors, logbook))
    fname = extract_content_between_tags(data, "image")
    link = extract_content_between_tags(data, "link")
    if fname == None and link != None:
        fname = link
    if fname != None:
        attachment[0] = fname
        attachment[1] = directory + "/" + link
        attachment[2] = get_mime_type(attachment[1])
        image_size = get_image_size(attachment[1])
        if debug > 0:
            print('Attachment: {0}'.format(attachment))
            if image_size:
                print("Image size: ", image_size)
    content = get_tagged(soup, "text")
    # convert from wiki markup to commonmark 
    commonmark = wiki2commonmark (content)
    if debug > 1:
        print("Logbook:", logbook)
        print ("=========\n"+commonmark+"=========")
    print(create_log_entry_with_attachments(url, logbook, owner, authors, timestamp, title, level, tags, commonmark, attachment, dry_run))
    #except Exception as e:
        #print(f"Error in {file_path}: {str(e)}")

if __name__ == "__main__":
    debug = 0
    main()
