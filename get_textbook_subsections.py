#! /usr/bin/env python3

'''
Extracts all the text content from each page of 
http://opendatastructures.org/ods-python/ for indexing
into Elasticsearch.

Creates a .jsonl file with a JSON object for 
each subsection of the textbook, and writes
this to the specified output file.
'''

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry #type: ignore
from requests_html import HTMLSession, HTMLResponse #type: ignore

import attr
from attr import attrs, attrib
from attr.validators import instance_of

import json
import regex as re #type: ignore

from typing import List, Dict, Tuple


TEXTBOOK_URL = 'http://opendatastructures.org/ods-python/Contents.html'


def get_session(retries: int = 3,
                backoff_factor: float = 0.1,
                status_forcelist: Tuple = (500, 502, 504)) -> HTMLSession:
    '''Gets an html session, using some default retry settings.'''
    session = HTMLSession()
    retry = Retry(total=retries, 
                  read=retries, 
                  connect=retries, 
                  backoff_factor=backoff_factor, 
                  status_forcelist=status_forcelist)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


def get_textbook_subsections() -> List[str]:
    '''Returns the urls of all subsections of the texboook. 
    Each subsection is displayed on its own webpage.
    '''
    session = get_session()
    r = session.get(TEXTBOOK_URL)
    base_url, contents  = TEXTBOOK_URL.rsplit('/', 1)
    chapters = get_chapter_page_names(r)
    # We will exclude the Bibliography and Index for our purposes
    chapters = [c for c in chapters if 'Bibliography' not in c and 'Index' not in c]
    chapter_urls = ['/'.join([base_url, chapter]) for chapter in chapters]
    subsections = []
    for chapter in chapter_urls:
        chapter_sections = get_all_subsections(session, chapter)
        chapter_sections = ['/'.join([base_url, cs]) for cs in chapter_sections]
        subsections.extend(chapter_sections)
    subsections.extend(chapter_urls)
    return subsections


def get_chapter_page_names(response: HTMLResponse) -> List[str]:
    '''Gets the page name for each chapter in the textbook'''
    lst, = response.html.find('body > ul')
    list_elements = lst.find('li')
    chapters = [li.find('a', first=True).attrs['href'] for li in list_elements]
    return chapters


def get_all_subsections(session: HTMLSession, url: str) -> List[str]:
    '''Gets the page name for each subsection in the given chapter.'''
    r = session.get(url) 
    body, = r.html.find('body')
    child_links, = body.find('ul.ChildLinks')
    items = child_links.find('li')
    subsections = [item.find('a', first=True).attrs['href'] for item in items]
    return subsections


def get_subsection_texts(pages: List[str]) -> List[Dict]:
    '''Gets the textual content from each subsection on a 
    given section webpage.

    Returns a list of dicts, one for each subsection.
    '''
    sections = []
    session = get_session()
    for page in pages:
        title, text = extract_title_and_text(page, session)
        text = remove_buttons(text)
        subsections = split_into_subsections(text)
        page_number, *_ = title.split()
        for section in subsections:
            s = {'id' : float(page_number), 
                 'subsection_number' : section.section_number,
                 'subsection_title' : section.subsection_title,
                 'title' : title, 
                 'text' : section.text}
            sections.append(s)
    return sections


def extract_title_and_text(url: str, session: HTMLSession) -> Tuple[str, str]:
    '''Extracts the title and text from one section of the textbook'''
    r = session.get(url)
    section_header, = r.html.find('body > h1')
    title = section_header.text
    section_text, = r.html.find('body > p')
    section_text = section_text.text
    return (title, section_text)


def remove_buttons(text: str) -> str:
    '''Removes the text from the menu at the bottom of 
    the page, and an footnotes that are included. 
    '''
    text, *_ = text.rsplit('\n\nNext: ', 1)
    text, *_ = text.rsplit('\nFootnotes\n', 1)
    text, *_ = text.rsplit('\n\n\nSubsections\n')
    return text
  

def split_into_subsections(text: str) -> List['Subsection']:
    '''Splits the text content extracted from a single textbook
    section into subsections.
    '''
    header = re.compile(r'^\d+\.\d+\.\d+(\.\d+)*')
    lines = text.split('\n')
    subsections = []
    current_section = Subsection()
    for line in lines:
        if m:=header.search(line):
            subsections.append(current_section)
            _, title = line.split(' ', 1)
            current_section = Subsection(m[0], title)
        current_section.add_line(line)
    subsections.append(current_section)
    return subsections


@attrs()
class Subsection:
    '''Represents a subsection within a single section (webpage) of the
    textbook. 

    Attributes
    ----------
    section_number: the number of the subsection
    lines: all lines that belong to this section
    text: the original representation of the section

    Methods
    -------
    add_line(line)
        Adds the input string to the list of lines
        in this section.


    '''
    section_number: str = attrib(validator=instance_of(str), default='0')
    subsection_title: str = attrib(validator=instance_of(str), default='')
    lines: List[str] = attrib(init=False, default=attr.Factory(list))
    _text: str = attrib(init=False)

    @property
    def text(self) -> str:
        text = '\n'.join(self.lines)
        self._text = text
        return self._text

    def add_line(self, line: str) -> None:
        self.lines.append(line)


def dump_to_file(sections: List[Dict], outfile: str) -> None:
    '''Writes input list of jsons to output .jsonl file'''
    with open(outfile, 'w', encoding='utf-8') as o:
        for s in sections:
            json.dump(s, o, ensure_ascii=False)
            o.write('\n')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description=__doc__
    )
    parser.add_argument('outfile', help='Path to the file that the text will be written to.')
    args = parser.parse_args()
    
    subsections = get_textbook_subsections()
    texts = get_subsection_texts(subsections)
    dump_to_file(texts, args.outfile)
