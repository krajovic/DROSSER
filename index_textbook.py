#! /usr/bin/env python3 

'''
Builds the Elasticsearch index that will be used for storing and 
querying documents throughout the system.
'''

import json

from elasticsearch import Elasticsearch

import tensorflow_hub as hub #type: ignore

import numpy as np #type: ignore

from typing import List

# load model that will generate embeddings
model = hub.load('https://tfhub.dev/google/universal-sentence-encoder/4')

def embedding(text: List[str]) -> List[np.array]:
    '''Get the Universal Sentence Encoder embedding.'''
    return np.array(model(text))


def build_index(infile: str) -> None:
    '''Adds each section of the textbook represented by a line
    in the JSON lines file to the Elasticsearch index. 

    Specifically each entry will have an id number, a section
    number, a subsection title, a main section title, the text
    and an embedding version of the text.
    '''
    with open(infile, 'r', encoding='utf-8') as f:
        es = Elasticsearch([{'host': 'localhost', 'port': 9200}])
        for i, line in enumerate(f, 1):
            section = json.loads(line)  # contains all info from the JSON
            emb = embedding([section['text']])
            section["text_vector"] = emb
            es.index(index='textbook', id=i, body=section)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description=__doc__
    )
    parser.add_argument('infile', help='Path to the JSON lines file output' +
                                        ' by get_textbook_subsections.py.')
    args = parser.parse_args()
    build_index(args.infile)
    