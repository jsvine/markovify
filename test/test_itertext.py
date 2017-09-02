import unittest
import markovify
import sys, os
import operator

class MarkovifyTest(unittest.TestCase):

    def test_simple(self):
        with open(os.path.join(os.path.dirname(__file__), "texts/sherlock.txt")) as f:
            sherlock_model = markovify.Text(f)
        sent = sherlock_model.make_sentence()
        assert sent is not None
        assert len(sent) != 0

    def test_without_retaining(self):
        with open(os.path.join(os.path.dirname(__file__), "texts/senate-bills.txt")) as f:
            senate_model = markovify.Text(f, retain_original=False)
        sent = senate_model.make_sentence()
        assert sent is not None
        assert len(sent) != 0

if __name__ == '__main__':
    unittest.main()


