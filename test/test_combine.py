import unittest
import markovify
import sys, os
import operator

def get_sorted(chain_json):
    return sorted(chain_json, key=operator.itemgetter(0))

class MarkovifyTest(unittest.TestCase):

    def setUp(self):
        with open(os.path.join(os.path.dirname(__file__), "texts/sherlock.txt")) as f:
            self.sherlock = f.read()

    def test_simple(self):
        text_model = markovify.Text(self.sherlock)
        combo = markovify.combine([ text_model, text_model ], [ 0.5, 0.5 ])
        assert(combo.chain.model == text_model.chain.model)

    def test_double_weighted(self):
        text_model = markovify.Text(self.sherlock)
        combo = markovify.combine([ text_model, text_model ])
        assert(combo.chain.model != text_model.chain.model)

if __name__ == '__main__':
    unittest.main()

