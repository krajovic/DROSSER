#! /usr/bin/env python3

from elasticsearch import Elasticsearch

import numpy as np # type: ignore

from typing import List, Dict, Optional

from query import Query


es = Elasticsearch([{'host': 'localhost', 'port': 9200}])

practice_keywords = {'practice', 'problem', 'problems', 'exericses', 
                     'exercise', 'sample', 'samples', 'examples', 
                     'example'}


def query_textbook(query: 'Query') -> Optional[Dict[str, str]]:
    '''Queries elasticsearch and returns the most 
    relevant section of the text.'''
    if requesting_practice(query):
        # add 'Discussion and Exercises' to the query to bias the 
        # initial section title based query towards exercises
        search_string = ' '.join([query.search_string.lower(), 'Discussion and Exercises'])
    else:
        search_string = query.search_string.lower()
    # query on chapter and subsection titles
    body = {'query': {'multi_match': 
                        {'query': search_string, 
                         'fields': ['title', 'subsection_title'], 
                         'fuzziness': 'AUTO'}}}
    r = es.search(index='textbook', body=body)['hits']['hits']
    # if we got no responses, query again based on full text
    if len(r) == 0:
        b = {'query': {'match': {'text': {'query': query.search_string, 'fuzziness': 'AUTO'}}}}
        r = es.search(index='textbook', body=b)['hits']['hits']
    # if there are still no responses, return None
    if len(r) == 0:
        return None
    # if the user is not asking for practice
    if not requesting_practice(query):
        # remove any Discussion and Exercises sections
        non_practice = only_non_practice(r)
        if len(non_practice) > 0:
            r = non_practice
    sims = np.zeros(len(r))     # holds cosine similarities
    # if the search string was only a few tokens, 
    # return the highest match according to elasticsearch
    if len(query.search_string.split(' ')) <= 2:
        res = r[0]
    # if the query was a longer string
    else:
        # compute cosine similarity between query and doc embedding
        for i, result in enumerate(r):
            doc_v = result['_source']['text_vector']
            sims[i] = cosine_similarity(doc_v[0], query.embedding)
        best = np.argmax(sims)
        res = r[best]
    return res['_source']


def cosine_similarity(v1: np.array, v2: np.array) -> float:
    '''Computes cosine similarity between two input vectors.'''
    return np.dot(v1, v2) / (np.sqrt(np.dot(v1,v1)) * np.sqrt(np.dot(v2,v2)))


def requesting_practice(query: 'Query') -> bool:
    '''Determines if query is requesting practice'''
    for word in practice_keywords:
        if word in query.search_string:
            return True
    return False


def only_non_practice(r: List[Dict[str, Dict[str, str]]]) -> List[Dict[str, Dict[str, str]]]:
    '''Retruns all results that are not
    Discussion and Exercises sections.'''
    return [s for s in r if 'Exercises' not in s['_source']['title']]


