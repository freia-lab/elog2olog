import sys
import os
import re
from bs4 import BeautifulSoup

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

def get_tagged(soup, tag):
    value = soup.find(tag)
    print(value)
    if (tag == "title"):
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
    for t in soup.find_all(True):
        print(t.name)
#    print (extract_content_between_tags(data, "link"))
#    print (soup)

if __name__ == "__main__":
    main()
