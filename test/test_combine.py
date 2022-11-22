import unittest
import markovify
import os
import operator


def get_sorted(chain_json):
    return sorted(chain_json, key=operator.itemgetter(0))


with open(os.path.join(os.path.dirname(__file__), "texts/sherlock.txt")) as f:
    sherlock = f.read()
    sherlock_model = markovify.Text(sherlock)
    sherlock_model_no_retain = markovify.Text(sherlock, retain_original=False)
    sherlock_model_compiled = sherlock_model.compile()
    sherlock_model_mp = markovify.Text(sherlock, multiprocess=True)
    sherlock_model_no_retain_mp = markovify.Text(
        sherlock, retain_original=False, multiprocess=True
    )
    sherlock_model_compiled_mp = sherlock_model_mp.compile()


class MarkovifyTest(unittest.TestCase):
    def test_simple(self):
        for text_model in (sherlock_model, sherlock_model_mp):
            combo = markovify.combine([text_model, text_model], [0.5, 0.5])
            assert combo.chain.model == text_model.chain.model

    def test_double_weighted(self):
        for text_model in (sherlock_model, sherlock_model_mp):
            combo = markovify.combine([text_model, text_model])
            assert combo.chain.model != text_model.chain.model

    def test_combine_chains(self):
        for model in (sherlock_model, sherlock_model_mp):
            chain = model.chain
            markovify.combine([chain, chain])

    def test_combine_dicts(self):
        for model in (sherlock_model, sherlock_model_mp):
            _dict = model.chain.model
            markovify.combine([_dict, _dict])

    def test_combine_lists(self):
        for model in (sherlock_model, sherlock_model_mp):
            _list = list(model.chain.model.items())
            markovify.combine([_list, _list])

    def test_bad_types(self):
        with self.assertRaises(Exception):
            markovify.combine(["testing", "testing"])

    def test_bad_weights(self):
        for text_model in (sherlock_model, sherlock_model_mp):
            with self.assertRaises(Exception):
                markovify.combine([text_model, text_model], [0.5])

    def test_mismatched_state_sizes(self):
        for multiprocess in (True, False):
            with self.assertRaises(Exception):
                text_model_a = markovify.Text(
                    sherlock, state_size=2, multiprocess=multiprocess
                )
                text_model_b = markovify.Text(
                    sherlock, state_size=3, multiprocess=multiprocess
                )
                markovify.combine([text_model_a, text_model_b])

    def test_mismatched_model_types(self):
        for multiprocess, model in ((True, sherlock_model_mp), (False, sherlock_model)):
            with self.assertRaises(Exception):
                text_model_a = model
                text_model_b = markovify.NewlineText(
                    sherlock, multiprocess=multiprocess
                )
                markovify.combine([text_model_a, text_model_b])

    def test_compiled_model_fail(self):
        for model_a, model_b in (
            (sherlock_model, sherlock_model_compiled),
            (sherlock_model_mp, sherlock_model_compiled_mp),
        ):
            with self.assertRaises(Exception):
                markovify.combine([model_a, model_b])

    def test_compiled_chain_fail(self):
        for model_a, model_b in (
            (sherlock_model.chain, sherlock_model_compiled.chain),
            (sherlock_model_mp.chain, sherlock_model_compiled_mp.chain),
        ):
            with self.assertRaises(Exception):
                markovify.combine([model_a, model_b])

    def test_combine_no_retain(self):
        for text_model in (sherlock_model_no_retain, sherlock_model_no_retain_mp):
            combo = markovify.combine([text_model, text_model])
            assert not combo.retain_original

    def test_combine_retain_on_no_retain(self):
        for text_model_a, text_model_b in (
            (sherlock_model_no_retain, sherlock_model),
            (sherlock_model_no_retain_mp, sherlock_model_mp),
        ):
            combo = markovify.combine([text_model_a, text_model_b])
            assert combo.retain_original
            assert combo.parsed_sentences == text_model_b.parsed_sentences

    def test_combine_no_retain_on_retain(self):
        for text_model_a, text_model_b in (
            (sherlock_model_no_retain, sherlock_model),
            (sherlock_model_no_retain_mp, sherlock_model_mp),
        ):
            combo = markovify.combine([text_model_b, text_model_a])
            assert combo.retain_original
            assert combo.parsed_sentences == text_model_b.parsed_sentences


if __name__ == "__main__":
    unittest.main()
