'''
Represents a query in our system. This is the representation of the 
question that a user enters that we will use throughout the system.
'''


from attr import attrs, attrib
from attr.validators import instance_of

import numpy as np #type: ignore

import re

# some basic stop words to help extract a list of keywords for search
STOP_WORDS = {'i', 'me', 'myself', 'we', 'our', 'ourselves', 'you', 'yours', 
'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', 'her', 'hers',
'herself', 'it', 'its', 'itself', 'they', 'them', 'themselves', 'what', 'which',
'who', 'whom', 'this', 'that', 'these', 'those', 'am', 'is', 'are', 'was', 'were', 
'be', 'being', 'been', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'does',
'doing', 'a', 'an', 'the', 'here', 'there', 'when', 'where', 'why', 'how', 'some', 
'will', 'can', 'should', 'could', 'work', 'understand', "don't", 'not', 'in', 
'on', 'for', 'by', 'with', 'near', 'among', 'to', 'need'}
 

@attrs()
class Query:
    '''Represents a query input by the user.

    Attributes
    ----------
    text: the original query string
    embedding: an embedding representation of the query
    search_string: a string of key words that will be used for search

    Methods
    -------
    _search_string_default()
        Generates the search string given the original input
        string my removing any token in the stopword set. 
    '''
    text: str = attrib(validator=instance_of(str), default='')
    embedding: np.array = attrib(default=None)
    search_string: str = attrib(init=False)

    @search_string.default
    def _search_string_default(self) -> str:
        tokens = self.text.lower().split()
        terms = [re.sub(r'[^\w]', '', t) for t in tokens if t not in STOP_WORDS]
        return ' '.join(terms)