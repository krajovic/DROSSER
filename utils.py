#! /usr/bin/evn python3

'''
Miscellaneous functions used in the converting the 
Open Data Structures textbook into a useable format 
for this project.
'''

import sys
import json

from bs4 import BeautifulSoup  #type: ignore

def post_process_textbook(infile: str, outfile: str) -> None:
    '''Removes the "Subsections" section of the text from each
    page stored in our .jsonl file because this did not information 
    that was relevant to the content on that page. 
    '''
    with open(infile, 'r', encoding='utf-8') as f, open(outfile, 'w+', encoding='utf-8') as o:
        for line in f:
            section = json.loads(line)
            chunks = section['text'].split('\n\n\nSubsections')
            if len(chunks) > 1:
                section['text'] = chunks[0]
            json.dump(section, o, ensure_ascii=False)
            o.write('\n')


def update_file_paths() -> None:
    '''Updates the file paths of the saved .html files'''
    for fp in sys.stdin:
        lines = []
        with open(fp.strip(), 'r', encoding='utf-8') as f:
            for line in f:
                if line != '\n':
                    lines.append(line.replace('./', 'static/'))
        with open(fp.strip(), 'w', encoding='utf-8') as o:
            for l in lines: 
                o.write(l)


def remove_nav_bar() -> None:
    '''Removes the navigation bar from each web page.'''
    for line in sys.stdin:
        with open(line.strip(), 'r') as f:
            soup = BeautifulSoup(f, 'html.parser')
            navs = soup.find_all('div', {'class': 'navigation'})
            sub = soup.find_all('a', {'name': 'CHILD_LINKS'})
            sects = soup.find_all('ul', {'class': 'ChildLinks'})
            for bar in navs:
                bar.decompose()
            for s in sub: 
                s.decompose()
            for sect in sects: 
                sect.decompose()
        with open(line.strip(), 'w') as o:
            o.write(str(soup))



