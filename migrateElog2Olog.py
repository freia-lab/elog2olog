import sys
import os
import re
import mimetypes
from datetime import datetime, timezone, timedelta
import requests
import json
import uuid
import pytz
from past.builtins import execfile

from requests_toolbelt.multipart.encoder import MultipartEncoder

from requests.auth import HTTPBasicAuth

import wikitextparser as wtp
from bs4 import BeautifulSoup

execfile('passwds.py')

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
        return "None"
    
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
    match = re.search(pattern, input_string)
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
    commonmark0 = input_data.replace("\n", "  \n")
    commonmark=""
    main_index = 0
    input_data_length = len(commonmark0)
    print ("DEBUG(wiki2commonmark): inp_data_length: " ,input_data_length)
    while main_index < input_data_length:
        print("DEBUG(wiki2commonmark): main_index: "+str(main_index)+"   Data@main_index: "+commonmark0[main_index:main_index+40])
        # Insert <newline> as the first character in order to make the search for tags
        # the same in the beginiing of the document as in hte rest of it
        indx, length, block = replace_tags("\n"+commonmark0[main_index:], "\n{{", "\n}}  \n", "\n```\n", "\n```\n")
        print ("DEBUG(wiki2commonmark): block_length, indx: " ,length, indx)
        if (indx >= 0):
            commonmark = commonmark + replace_formatting(commonmark0[main_index:main_index+indx])
            commonmark = commonmark + block
            main_index = main_index + length + indx - 1
            print("DEBUG(wiki2commonmark): main_index after the last code block:", main_index)
        else:
            commonmark = commonmark + replace_formatting(commonmark0[main_index:])
            break
    return commonmark

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

def get_owner(data):
    dict = {"KG":"KG", "KF": "KF", "Kf": "KF"}
    others = ""
    guest = "konrad"
    a = extract_content_between_tags(data, "author")
    print (a[0:2])
    if a[0:2] in dict:
        if len(a) == 2:
            return dict[a], others
        else:
            return dict[a[0:2]], "Author(s): "+a+"  \n"
    else:
        return guest,""
 
def get_title(data):
    t = extract_content_between_tags(data, "title")
    return t

def get_tag(data):
    k = extract_content_between_tags(data, "keywords")
    return k

def get_level(data):
    l = extract_content_between_tags(data, "severity")
    if (l == "NONE"):
        l = "Normal"
    return l

def create_log_entry_with_attachments(api_endpoint, logbook, owner, authors, timestamp, title, level, tags, descr, attachment):
    # Prepare log entry payload
    if (attachment[0] == "None"):
        log_entry = {
            "description": authors+descr,
            "level": level,
            "title": title,
            "logbooks": [{"name": logbook}],
            "events": [{"name":"OriginalCreatedDate","instant": timestamp }]
        }
    else:
        log_entry = {
            "description": "New entry using Olog/logs/multipart with one embedded image attachment.\n\n![](attachment/"+attchmntId+"){width=140 height=67}",
            "level": level,
            "title": title,
            "logbooks": [{"name": logbook}],
            "events": [{"name":"OriginalCreatedDate","instant": timestamp }],
            "attachments":[
            {"id": attchmntId, "filename": attachment[1][0]}
            ]
        }
         # Prepare the attachment
        attachment = ('files', ('FREIAlogo-v3_March19.png', open('FREIAlogo-v3_March19.png', 'rb'), 'image/png'))
        attchmntId = str(uuid.uuid4())

        #print (attachment[1][0])
        #print (attachment[0] + ": ", attachment[1])
        # Prepare the log entry payload as JSON
        json_filename = json.dumps({"filename": attachment[0]})
        json_descr = json.dumps({"fileMetadataDescription": attachment[2]})
    #print (log_entry)

    # Prepare the log entry payload as JSON
    json_data = json.dumps(log_entry)
    # Prepare the multipart encoder
    if (attachment[0] == "None"):
        multipart_data = MultipartEncoder(
            fields={
                'logEntry': ('logEntry.json', json_data, 'application/json')
            }
        )
    else:
        multipart_data = MultipartEncoder(
            fields={
                'logEntry': ('logEntry.json', json_data, 'application/json'),
                'files': ('filename', json_filename, 'application/json'),
                'files': ('fileMetadataDescription', json_descr, 'application/json'),
                'files': (attachment[0], open(attachment[1], 'rb'), 'application/octet-stream')
            }
        )
    
    # Set the Content-Type header with the boundary
    headers = {
        'Content-Type': multipart_data.content_type
    }
    print("Content-Type " + multipart_data.content_type)
    #print(multipart_data)
    try:
        response = requests.put(api_endpoint, headers=headers, data=multipart_data, auth=HTTPBasicAuth(owner, dict[owner]))
        if response.status_code == 200:
            print("Log entry created successfully.")
        else:
            print(f"Failed to create log entry. Status code: {response.status_code}")
    except Exception as e:
        print("An error occurred: ",{str(e)})

def main():
    
    attachment = ["None","None","None"]
     # Default values for url and logbook
    url = "https://freia-olog.physics.uu.se:8181/Olog/logs/multipart"
    logbook = "test"
   
    if len(sys.argv) < 2:
        print("Usage: python3 migrateElog2Olog.py <file_path> [-l <logbook>] [-u <url>]")
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
        else:
            print("Error: Invalid option", sys.argv[i])
            return

        #    print("Directory:", directory)
        #    print("File Name:", filename)
    try:
        owner, authors = get_owner(data)
        title = get_title(data)
        level = get_level(data)
        tags = get_tag(data)
        d =  extract_content_between_tags(data, "isodate")
        t = extract_content_between_tags(data, "time")
        timestamp = datetime_to_unix_milliseconds(d,t)
        print('Author: {1}\tTitle: {0}\nLevel: {2!s:.<20s}Keyword: {3!s:.<20s}Timestamp: {4}'.format(title,owner,level,tags,timestamp))
        fname = extract_content_between_tags(data, "image")
        attachment[0] = fname
        if fname != "None":
            attachment = directory + "/" + extract_content_between_tags(data, "link")
            # print ("Attachment: "+fname+"  \t\t\t"+attachment+" ("+get_mime_type(attachment)+")")
            print('Attachment: {0!s:.<40}{1!s:.<60s}{2}'.format(fname, attachment, get_mime_type(attachment)))
        else:
            print("Attachment: "+fname)
        content = get_tagged(soup, "text")
        # convert from wiki markup to commonmark 
        #  print(content.replace("\n", "  \n"))
        #print (dir(content))
        # convert from wiki markup to commonmark 
        commonmark = wiki2commonmark (content)
        print ("=========\n"+commonmark+"=========")
        create_log_entry_with_attachments(url, logbook, owner, authors, timestamp, title, level, tags, commonmark, attachment)
        #print("Logbook:", logbook)
    except Exception as e:
        print(f"Error in {file_path}: {str(e)}")

if __name__ == "__main__":
    main()
