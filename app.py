#! /usr/bin/env python3

from flask import Flask, request, render_template 

from bs4 import BeautifulSoup #type: ignore

import tensorflow_hub as hub #type: ignore

import numpy as np # type: ignore

from search import query_textbook

from query import Query

import json
import sys
import signal

from transformers import pipeline #type: ignore

from typing import Dict, Tuple, List

from pathlib import Path


app = Flask(__name__)

QUESTION_WORDS = {'who', 'what', 'when', 'where', 'why', 'how', 'which'}
MIN_SENT_LENGTH = 100

metrics = {'1': 0, '2' : 0, '3' : 0, '4' : 0, '5' : 0}


@app.route('/', methods=['GET', 'POST'])
def home() -> str:
    '''Displays home page for the app.'''
    return render_template('home.html')


@app.route('/display_section', methods=["POST"])
def display_section() -> str:
    '''Displays the section most relevant to the query.'''
    query_text = request.form['query']
    if not query_text:
        return render_template('section.html', 
                               section='<p>Please input a question!</p>', 
                               question=query_text, 
                               metrics=False)
    else:
        emb = embedding([query_text])
        query = Query(query_text, emb)
        #response = get_resource(query)
        response = query_textbook(query)
        if response is None:
            return render_template('section.html', 
                                    error='We could not find any results, please enter another question.',
                                    question=query_text, 
                                    answer='', 
                                    title='', 
                                    metrics=False)
        fp, title = get_subsection_info(response)
        #fp, score, section, title = response
        answer = qa(query, response)
        with open(fp, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')
        return render_template('section.html', 
                               section=soup, 
                               question=query_text, 
                               answer=answer, 
                               title=title, 
                               metrics=True)


@app.route('/update_metrics', methods=['POST'])
def update_metrics() -> str:
    '''Updates metrics according to users rating and 
    returns to the home page.
    '''
    evaluation = request.form['metrics']
    metrics[evaluation] += 1
    return render_template('home.html')


def qa(query: 'Query', section: Dict[str, str]) -> str:
    '''Performs question answering on an input query and 
    section of text.'''
    answer = ''
    if any(x in query.text.lower() for x in QUESTION_WORDS):        # if the input is a question
        paras = section['text'].splitlines()                        # split the section into paragraphs
        worth_checking = [line for line in paras if len(line) > MIN_SENT_LENGTH]  # take all lines with substantial content
        worth_checking = (worth_checking if len(worth_checking) > 0 else [section['text']])
        best_answer: Dict[str, str] = {}
        for elem in worth_checking:
            q = (''.join([query.text, '?']) if not query.text.endswith('?') else query.text)
            a = nlp(question=q, context=elem)      # run QA on each paragraph
            if best_answer == {} or a['score'] > best_answer['score']: 
                best_answer = a
        if best_answer != {}:
            answer = best_answer['answer']
    return answer


def embedding(text: List[str]) -> np.array:
    '''Looks up the sentence embedding for the query.'''
    return np.array(model(text)[0])


def get_subsection_info(section: Dict[str, str]) -> Tuple[str, str]:
    '''Gets file path to the relevant page
    and the subsection title.'''
    page_title = section['title']
    t = page_title.replace(':', '_')
    fp = ''.join(['templates/Book/', t, '.html'])
    if section['subsection_number'] == '0':
        sub_title = section['title']
    else:
        sub_title = " ".join([section['subsection_number'], section['subsection_title']])
    return fp, sub_title



def load_metrics() -> None:
    '''Loads metrics from stored metrics file.'''
    p = Path('metrics.json')
    if p.exists():
        with p.open('r', encoding='utf-8') as f:
            d = json.load(f)
            metrics = d


def dump_metrics() -> None:
    '''Writes metrics to metrics file.'''
    with open('metrics.json', 'w', encoding='utf-8') as f:
        json.dump(metrics, f, ensure_ascii=False)


def exit_handler(signal, frame):
    '''Ensures that metrics are dumped to metrics file before exiting'''
    dump_metrics()
    sys.exit(0)


if __name__ == '__main__':
    # on ctrl-C send to handler
    signal.signal(signal.SIGINT, exit_handler)
    # question answering from huggingface
    nlp = pipeline('question-answering')
    # Universal Sentence Encoder embeddings
    model = hub.load('https://tfhub.dev/google/universal-sentence-encoder/4')
    load_metrics()
    app.run(debug=True)