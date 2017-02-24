import unittest
import markovify
import sys
import os
import operator


def get_sorted(chain_json):
    return sorted(chain_json, key=operator.itemgetter(0))


class MarkovifyTest(unittest.TestCase):

    def setUp(self):
        with open(os.path.join(os.path.dirname(__file__), "texts/sherlock.txt")) as f:
            self.sherlock = f.read()

    def test_text_too_small(self):
        text = u"Example phrase. This is another example sentence."
        text_model = markovify.Text(text)
        assert(text_model.make_sentence() is None)

    def test_sherlock(self):
        text_model = markovify.Text(self.sherlock)
        sent = text_model.make_sentence()
        assert(len(sent) != 0)

    def test_json(self):
        text_model = markovify.Text(self.sherlock)
        json_model = text_model.to_json()
        new_text_model = markovify.Text.from_json(json_model)
        sent = text_model.make_sentence()
        assert(len(sent) != 0)

    def test_chain(self):
        text_model = markovify.Text(self.sherlock)
        chain_json = text_model.chain.to_json()

        stored_chain = markovify.Chain.from_json(chain_json)
        assert(get_sorted(stored_chain.to_json()) == get_sorted(chain_json))

        new_text_model = markovify.Text.from_chain(chain_json)
        assert(get_sorted(new_text_model.chain.to_json()) == get_sorted(chain_json))

        sent = new_text_model.make_sentence()
        assert(len(sent) != 0)

    def test_make_sentence_with_start(self):
        text_model = markovify.Text(self.sherlock)
        start_str = "Sherlock Holmes"
        sent = text_model.make_sentence_with_start(start_str)
        assert(sent is not None)
        assert(start_str == sent[:len(start_str)])

    def test_make_sentence_with_start_one_word(self):
        text_model = markovify.Text(self.sherlock)
        start_str = "Sherlock"
        sent = text_model.make_sentence_with_start(start_str)
        assert(sent is not None)
        assert(start_str == sent[:len(start_str)])

    def test_make_sentence_with_start_three_words(self):
        start_str = "Sherlock Holmes was"
        text_model = markovify.Text(self.sherlock)
        try:
            text_model.make_sentence_with_start(start_str)
            assert(False)
        except markovify.text.ParamError:
            assert(True)
        text_model = markovify.Text(self.sherlock, state_size=3)
        text_model.make_sentence_with_start(start_str)
        text_model.make_sentence_with_start("Sherlock")

    def test_short_sentence(self):
        text_model = markovify.Text(self.sherlock)
        sent = None
        while sent is None:
            sent = text_model.make_short_sentence(45)
        assert len(sent) < 45


if __name__ == '__main__':
    unittest.main()
