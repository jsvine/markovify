import unittest
import markovify
import sys, os
import operator

def get_sorted(chain_json):
    return sorted(chain_json, key=operator.itemgetter(0))

with open(os.path.join(os.path.dirname(__file__), "texts/sherlock.txt")) as f:
    sherlock = f.read()
    sherlock_model = markovify.Text(sherlock)
    sherlock_model_no_retain = markovify.Text(sherlock, retain_original=False)

class MarkovifyTest(unittest.TestCase):

    def test_simple(self):
        text_model = sherlock_model
        combo = markovify.combine([ text_model, text_model ], [ 0.5, 0.5 ])
        assert(combo.chain.model == text_model.chain.model)

    def test_double_weighted(self):
        text_model = sherlock_model
        combo = markovify.combine([ text_model, text_model ])
        assert(combo.chain.model != text_model.chain.model)

    def test_combine_chains(self):
        chain = sherlock_model.chain
        combo = markovify.combine([ chain, chain ])

    def test_combine_dicts(self):
        _dict = sherlock_model.chain.model
        combo = markovify.combine([ _dict, _dict ])

    def test_combine_lists(self):
        _list = list(sherlock_model.chain.model.items())
        combo = markovify.combine([ _list, _list ])

    def test_bad_types(self):
        with self.assertRaises(Exception) as context:
            combo = markovify.combine([ "testing", "testing" ])

    def test_bad_weights(self):
        with self.assertRaises(Exception) as context:
            text_model = sherlock_model
            combo = markovify.combine([ text_model, text_model ], [ 0.5  ])

    def test_mismatched_state_sizes(self):
        with self.assertRaises(Exception) as context:
            text_model_a = markovify.Text(sherlock, state_size=2)
            text_model_b = markovify.Text(sherlock, state_size=3)
            combo = markovify.combine([ text_model_a, text_model_b ])

    def test_mismatched_model_types(self):
        with self.assertRaises(Exception) as context:
            text_model_a = sherlock_model
            text_model_b = markovify.NewlineText(sherlock)
            combo = markovify.combine([ text_model_a, text_model_b ])

    def test_combine_no_retain(self):
        text_model = sherlock_model_no_retain
        combo = markovify.combine([ text_model, text_model ])
        assert(not combo.retain_original)

    def test_combine_retain_on_no_retain(self):
        text_model_a = sherlock_model_no_retain
        text_model_b = sherlock_model
        combo = markovify.combine([ text_model_a, text_model_b ])
        assert(combo.retain_original)
        assert(combo.parsed_sentences == text_model_b.parsed_sentences)

    def test_combine_no_retain_on_retain(self):
        text_model_a = sherlock_model_no_retain
        text_model_b = sherlock_model
        combo = markovify.combine([ text_model_b, text_model_a ])
        assert(combo.retain_original)
        assert(combo.parsed_sentences == text_model_b.parsed_sentences)

if __name__ == '__main__':
    unittest.main()

