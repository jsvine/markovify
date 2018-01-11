import operator
import os
import sys
import unittest

import markovify
from markovify.chain import BEGIN, END

def get_sorted(chain_json):
    return sorted(chain_json, key=operator.itemgetter(0))

with open(os.path.join(os.path.dirname(__file__), "texts/sherlock.txt")) as f:
    sherlock = f.read()
    sherlock_model = markovify.Text(sherlock)

class MarkovifyTest(unittest.TestCase):

    def test_text_too_small(self):
        text = u"Example phrase. This is another example sentence."
        text_model = markovify.Text(text)
        assert(text_model.make_sentence() == None)

    def test_sherlock(self):
        text_model = sherlock_model
        sent = text_model.make_sentence()
        assert(len(sent) != 0)

    def test_json(self):
        text_model = sherlock_model
        json_model = text_model.to_json()
        new_text_model = markovify.Text.from_json(json_model)
        sent = text_model.make_sentence()
        assert(len(sent) != 0)

    def test_chain(self):
        text_model = sherlock_model
        chain_json = text_model.chain.to_json()

        stored_chain = markovify.Chain.from_json(chain_json)
        assert(get_sorted(stored_chain.to_json()) == get_sorted(chain_json))

        new_text_model = markovify.Text.from_chain(chain_json)
        assert(get_sorted(new_text_model.chain.to_json()) == get_sorted(chain_json))

        sent = new_text_model.make_sentence()
        assert(len(sent) != 0)

    def test_make_sentence_with_start(self):
        text_model = sherlock_model
        start_str = "Sherlock Holmes"
        sent = text_model.make_sentence_with_start(start_str)
        assert(sent != None)
        assert(start_str == sent[:len(start_str)])

    def test_make_sentence_with_start_one_word(self):
        text_model = sherlock_model
        start_str = "Sherlock"
        sent = text_model.make_sentence_with_start(start_str)
        assert(sent != None)
        assert(start_str == sent[:len(start_str)])

    def test_make_sentence_with_start_one_word_that_doesnt_begin_a_sentence(self):
        text_model = sherlock_model
        start_str = "dog"
        with self.assertRaises(KeyError) as context:
            sent = text_model.make_sentence_with_start(start_str)

    def test_make_sentence_with_word_not_at_start_of_sentence(self):
        text_model = sherlock_model
        start_str = "dog"
        sent = text_model.make_sentence_with_start(start_str, strict=False)
        assert(sent != None)
        assert(start_str == sent[:len(start_str)])

    def test_make_sentence_with_words_not_at_start_of_sentence(self):
        text_model = markovify.Text(sherlock, state_size=3)
        # " I was " has 128 matches in sherlock.txt
        # " was I " has 2 matches in sherlock.txt
        start_str = "was I"
        sent = text_model.make_sentence_with_start(start_str, strict=False, tries=50)
        assert(sent != None)
        assert(start_str == sent[:len(start_str)])

    def test_make_sentence_with_words_not_at_start_of_sentence_miss(self):
        text_model = markovify.Text(sherlock, state_size=3)
        start_str = "was werewolf"
        sent = text_model.make_sentence_with_start(start_str, strict=False, tries=50)
        assert(sent == None)

    def test_make_sentence_with_words_not_at_start_of_sentence_of_state_size(self):
        text_model = markovify.Text(sherlock, state_size=2)
        start_str = "was I"
        sent = text_model.make_sentence_with_start(start_str, strict=False, tries=50)
        assert(sent != None)
        assert(start_str == sent[:len(start_str)])

    def test_make_sentence_with_words_to_many(self):
        text_model = sherlock_model
        start_str = "dog is good"
        with self.assertRaises(markovify.text.ParamError) as context:
            sent = text_model.make_sentence_with_start(start_str, strict=False)

    def test_make_sentence_with_start_three_words(self):
        start_str = "Sherlock Holmes was"
        text_model = sherlock_model
        try:
            text_model.make_sentence_with_start(start_str)
            assert(False)
        except markovify.text.ParamError:
            assert(True)
        text_model = markovify.Text(sherlock, state_size=3)
        text_model.make_sentence_with_start(start_str)
        sent = text_model.make_sentence_with_start("Sherlock")
        assert(markovify.chain.BEGIN not in sent)

    def test_short_sentence(self):
        text_model = sherlock_model
        sent = None
        while sent is None:
            sent = text_model.make_short_sentence(45)
        assert len(sent) <= 45

    def test_short_sentence_min_chars(self):
        sent = None
        while sent is None:
            sent = sherlock_model.make_short_sentence(100, min_chars=50)
        assert len(sent) <= 100
        assert len(sent) >= 50

    def test_dont_test_output(self):
        text_model = sherlock_model
        sent = text_model.make_sentence(test_output=False)
        assert sent is not None

    def test_max_words(self):
        text_model = sherlock_model
        sent = text_model.make_sentence(max_words=0)
        assert sent is None

    def test_newline_text(self):
        with open(os.path.join(os.path.dirname(__file__), "texts/senate-bills.txt")) as f:
            model = markovify.NewlineText(f.read())
        model.make_sentence()

    def test_bad_corpus(self):
        with self.assertRaises(Exception) as context:
            markovify.Chain(corpus="testing, testing", state_size=2)

    def test_bad_json(self):
        with self.assertRaises(Exception) as context:
            markovify.Chain.from_json(1)

    def test_chain_update(self):
        chain = markovify.Chain([["foo", "bar"]], state_size=1)
        assert len(chain.model.keys()) == 3
        assert "testing" not in chain.begin_choices

        chain.update([["testing", "testing"]])
        assert len(chain.model.keys()) == 4
        assert "testing" in chain.begin_choices

    def test_text_update(self):
        text_model = sherlock_model
        orig_parsed_sent_len = len(text_model.parsed_sentences)
        orig_rejoined_text_len = len(text_model.rejoined_text)

        text_model.update(sherlock)
        assert len(text_model.parsed_sentences) > orig_parsed_sent_len
        assert len(text_model.rejoined_text) > orig_rejoined_text_len

    def test_none_text(self):
        text_model = markovify.Text(None)
        assert text_model.chain.model == {}
        assert not hasattr(text_model, 'parsed_sentences')
        assert text_model.make_sentence() == ''

    def test_empty_text_retain(self):
        text_model = markovify.Text('', state_size=1)
        assert text_model.chain.model == {}
        assert text_model.parsed_sentences == []
        assert text_model.rejoined_text == ''
        # generated sentence: '' was rejected since it matches rejoined_text
        assert text_model.make_sentence() is None

    def test_empty_text_no_retain(self):
        text_model = markovify.Text('', state_size=1, retain_original=False)
        assert text_model.chain.model == {}
        assert not hasattr(text_model, 'parsed_sentences')
        assert text_model.make_sentence() == ''

if __name__ == '__main__':
    unittest.main()
