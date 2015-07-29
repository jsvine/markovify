import random
import markovify
import sys, os

HERE = os.path.dirname(os.path.realpath(__file__))

def test_text_too_small():
    text = u"Example phrase. This is another example sentence."
    text_model = markovify.Text(text)
    assert(text_model.make_sentence() == None)

def test_sherlock():
    with open(os.path.join(HERE, "texts/sherlock.txt")) as f:
        text = f.read()
    text_model = markovify.Text(text)
    sent = text_model.make_sentence()
    assert(len(sent) != 0)
