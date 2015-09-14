import random
import markovify
import sys, os
import operator

HERE = os.path.dirname(os.path.realpath(__file__))
with open(os.path.join(HERE, "texts/sherlock.txt")) as f:
    sherlock = f.read()

def test_text_too_small():
    text = u"Example phrase. This is another example sentence."
    text_model = markovify.Text(text)
    assert(text_model.make_sentence() == None)

def test_sherlock():
    text_model = markovify.Text(sherlock)
    sent = text_model.make_sentence()
    assert(len(sent) != 0)

def get_sorted(chain_json):
    return sorted(chain_json, key=operator.itemgetter(0))

def test_json():
    text_model = markovify.Text(sherlock)
    chain_json = text_model.chain.to_json()
    stored_chain = markovify.Chain.from_json(chain_json)
    assert(get_sorted(stored_chain.to_json()) == get_sorted(chain_json))
    new_text_model = markovify.Text(sherlock, chain=stored_chain)
    sent = text_model.make_sentence()
    assert(len(sent) != 0)

def test_make_sentence_with_start():
    text_model = markovify.Text(sherlock)
    sent = text_model.make_sentence_with_start("Sherlock Holmes")
    assert(sent != None)
