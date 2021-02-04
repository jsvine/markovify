import unittest
from pathlib import Path

import markovify


TEXTS = Path(__file__).resolve().parent / 'texts'


class MarkovifyTest(unittest.TestCase):

    @staticmethod
    def test_simple():
        sherlock_model = markovify.Text((TEXTS / 'sherlock.txt').read_text())
        sent = sherlock_model.make_sentence()
        assert sent is not None
        assert len(sent) != 0

    @staticmethod
    def test_without_retaining():
        senate_model = markovify.Text((TEXTS / 'senate-bills.txt').read_text(),
                                      retain_original=False)
        sent = senate_model.make_sentence()
        assert sent is not None
        assert len(sent) != 0

    @staticmethod
    def test_from_json_without_retaining():
        senate_model = markovify.Text((TEXTS / 'senate-bills.txt').read_text(),
                                      retain_original=False)
        d = senate_model.to_json()
        new_model = markovify.Text.from_json(d)
        sent = new_model.make_sentence()
        assert sent is not None
        assert len(sent) != 0

    @staticmethod
    def test_from_mult_files_without_retaining():
        models = []
        for path in TEXTS.glob('*.txt'):
            models.append(markovify.Text(path.read_text(),
                                         retain_original=False))
        combined_model = markovify.combine(models)
        sent = combined_model.make_sentence()
        assert sent is not None
        assert len(sent) != 0


if __name__ == '__main__':
    unittest.main()
