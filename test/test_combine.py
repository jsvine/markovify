import operator
import unittest
from pathlib import Path

import markovify


TEXTS = Path(__file__).resolve().parent / 'texts'


def get_sorted(chain_json):
    return sorted(chain_json, key=operator.itemgetter(0))


sherlock_text = (TEXTS / 'sherlock.txt').read_text()
sherlock_model = markovify.Text(sherlock_text)
sherlock_model_no_retain = markovify.Text(sherlock_text, retain_original=False)
sherlock_model_compiled = sherlock_model.compile()


class MarkovifyTest(unittest.TestCase):

    @staticmethod
    def test_simple():
        text_model = sherlock_model
        combo = markovify.combine([text_model, text_model], [0.5, 0.5])
        assert combo.chain.model == text_model.chain.model

    @staticmethod
    def test_double_weighted():
        text_model = sherlock_model
        combo = markovify.combine([text_model, text_model])
        assert combo.chain.model != text_model.chain.model

    @staticmethod
    def test_combine_chains():
        chain = sherlock_model.chain
        markovify.combine([chain, chain])

    @staticmethod
    def test_combine_dicts():
        _dict = sherlock_model.chain.model
        markovify.combine([_dict, _dict])

    @staticmethod
    def test_combine_lists():
        _list = list(sherlock_model.chain.model.items())
        markovify.combine([_list, _list])

    def test_bad_types(self):
        with self.assertRaises(Exception):
            markovify.combine(["testing", "testing"])

    def test_bad_weights(self):
        with self.assertRaises(Exception):
            text_model = sherlock_model
            markovify.combine([text_model, text_model], [0.5])

    def test_mismatched_state_sizes(self):
        with self.assertRaises(Exception):
            text_model_a = markovify.Text(sherlock_text, state_size=2)
            text_model_b = markovify.Text(sherlock_text, state_size=3)
            markovify.combine([text_model_a, text_model_b])

    def test_mismatched_model_types(self):
        with self.assertRaises(Exception):
            text_model_a = sherlock_model
            text_model_b = markovify.NewlineText(sherlock_text)
            markovify.combine([text_model_a, text_model_b])

    def test_compiled_model_fail(self):
        with self.assertRaises(Exception):
            model_a = sherlock_model
            model_b = sherlock_model_compiled
            markovify.combine([model_a, model_b])

    def test_compiled_chain_fail(self):
        with self.assertRaises(Exception):
            model_a = sherlock_model.chain
            model_b = sherlock_model_compiled.chain
            markovify.combine([model_a, model_b])

    @staticmethod
    def test_combine_no_retain():
        text_model = sherlock_model_no_retain
        combo = markovify.combine([text_model, text_model])
        assert not combo.retain_original

    @staticmethod
    def test_combine_retain_on_no_retain():
        text_model_a = sherlock_model_no_retain
        text_model_b = sherlock_model
        combo = markovify.combine([text_model_a, text_model_b])
        assert combo.retain_original
        assert combo.parsed_sentences == text_model_b.parsed_sentences

    @staticmethod
    def test_combine_no_retain_on_retain():
        text_model_a = sherlock_model_no_retain
        text_model_b = sherlock_model
        combo = markovify.combine([text_model_b, text_model_a])
        assert combo.retain_original
        assert combo.parsed_sentences == text_model_b.parsed_sentences


if __name__ == '__main__':
    unittest.main()
