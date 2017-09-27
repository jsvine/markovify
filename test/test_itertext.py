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

    def test_from_json_without_retaining(self):
        with open(os.path.join(os.path.dirname(__file__), "texts/senate-bills.txt")) as f:
            original_model = markovify.Text(f, retain_original=False)
        d = original_model.to_json()
        new_model = markovify.Text.from_json(d)
        sent = new_model.make_sentence()
        assert sent is not None
        assert len(sent) != 0

    def test_from_mult_files_without_retaining(self):
        models = []
        for (dirpath, _, filenames) in os.walk(os.path.join(os.path.dirname(__file__), "texts")):
            for filename in filenames:
                with open(os.path.join(dirpath, filename)) as f:
                    models.append(markovify.Text(f, retain_original=False))
        combined_model = markovify.combine(models)
        sent = combined_model.make_sentence()
        assert sent is not None
        assert len(sent) != 0

if __name__ == '__main__':
    unittest.main()


