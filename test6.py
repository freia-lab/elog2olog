import requests
import json
import uuid
from requests_toolbelt.multipart.encoder import MultipartEncoder

from requests.auth import HTTPBasicAuth

username = 'konrad'
password = '*****'

def create_log_entry_with_attachments():
    api_endpoint = "https://freia-olog.physics.uu.se:8181/Olog/logs/multipart"

    # Prepare the attachment
    attachment = ('files', ('FREIAlogo-v3_March19.png', open('FREIAlogo-v3_March19.png', 'rb'), 'image/png'))
    attchmntId = str(uuid.uuid4())
    # Prepare log entry payload
    log_entry = {
        "owner": "dev",
        "description": "New entry using Olog/logs/multipart with one embedded image attachment.\n\n![](attachment/"+attchmntId+"){width=140 height=67}",
        "level": "INFO",
        "title": "test6.py",
        "logbooks": [{"name": "test"}],
        "attachments":[
            {"id": attchmntId, "filename": attachment[1][0]}
        ]
    }


    print (attachment[1][0])
    print (attachment[0] + ": ", attachment[1])
    print (log_entry)

    # Prepare the log entry payload as JSON
    json_data = json.dumps(log_entry)
    json_filename = json.dumps({"filename": "FREIAlogo-v3_March19.png"})
    json_descr = json.dumps({"fileMetadataDescription": "image/png"})

    # Prepare the multipart encoder
    multipart_data = MultipartEncoder(
        fields={
            'logEntry': ('logEntry.json', json_data, 'application/json'),
            'files': ('filename', json_filename, 'application/json'),
            'files': ('fileMetadataDescription', json_descr, 'application/json'),
#            'files': ('file', ('FREIAlogo-v3_March19.png', open('FREIAlogo-v3_March19.png', 'rb'), 'image/png'), 'application/octet-stream')
            'files': ('FREIAlogo-v3_March19.png', open('FREIAlogo-v3_March19.png', 'rb'), 'application/octet-stream')
        }
    )

    # Set the Content-Type header with the boundary
    headers = {
        'Content-Type': multipart_data.content_type
    }
    print("Content-Type " + multipart_data.content_type)
    print(multipart_data)
    try:
        response = requests.put(api_endpoint, headers=headers, data=multipart_data, auth=HTTPBasicAuth(username, password))
        if response.status_code == 200:
            print("Log entry without attachments created successfully.")
        else:
            print(f"Failed to create log entry. Status code: {response.status_code}")
    except Exception as e:
        print("An error occurred: ",{str(e)})

if __name__ == "__main__":
    create_log_entry_with_attachments()
