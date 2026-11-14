import unittest

import markovify


class TaggedText(markovify.NewlineText):
    def word_join(self, words):
        return " ".join(word.split("::")[0] for word in words)


class ConfiguredText(markovify.NewlineText):
    def __init__(self, input_text, separator, **kwargs):
        self.separator = separator
        super().__init__(input_text, **kwargs)

    def word_join(self, words):
        return self.separator.join(words)


class TestCompileSubclass(unittest.TestCase):
    corpus = "alpha::N beta::V gamma::N\ndelta::N epsilon::V zeta::N"

    def test_compile_preserves_subclass(self):
        model = markovify.NewlineText("alpha beta gamma\ndelta epsilon zeta")
        compiled = model.compile()
        self.assertIs(type(compiled), markovify.NewlineText)
        self.assertEqual(compiled.sentence_split("alpha\nbeta"), ["alpha", "beta"])

    def test_compiled_output_uses_custom_word_join(self):
        model = TaggedText(self.corpus)
        expected = model.make_sentence_with_start("alpha::N beta::V", test_output=False)
        self.assertEqual(expected, "alpha beta gamma")
        self.assertEqual(
            model.compile().make_sentence_with_start(
                "alpha::N beta::V", test_output=False
            ),
            expected,
        )

    def test_compile_preserves_constructor_configuration(self):
        model = ConfiguredText("alpha beta gamma", separator="|")
        compiled = model.compile()
        self.assertEqual(
            compiled.make_sentence_with_start("alpha beta", test_output=False),
            "alpha|beta|gamma",
        )
        self.assertEqual(compiled.separator, "|")

    def test_compile_without_original_text_preserves_custom_output(self):
        model = TaggedText(self.corpus, retain_original=False)
        compiled = model.compile()
        self.assertFalse(compiled.retain_original)
        self.assertFalse(hasattr(compiled, "parsed_sentences"))
        self.assertEqual(
            compiled.make_sentence_with_start("alpha::N beta::V", test_output=False),
            "alpha beta gamma",
        )

    def test_recompile_preserves_custom_output(self):
        model = TaggedText(self.corpus).compile().compile()
        self.assertEqual(
            model.make_sentence_with_start("alpha::N beta::V", test_output=False),
            "alpha beta gamma",
        )

    def test_compile_leaves_original_chain_uncompiled(self):
        model = TaggedText(self.corpus)
        original_chain = model.chain
        compiled = model.compile()
        self.assertIs(model.chain, original_chain)
        self.assertIsNot(compiled.chain, original_chain)
        self.assertFalse(model.chain.compiled)
        self.assertTrue(compiled.chain.compiled)
        self.assertEqual(model.chain.walk(("alpha::N", "beta::V")), ["gamma::N"])

    def test_compile_in_place_preserves_subclass_and_configuration(self):
        model = ConfiguredText("alpha beta gamma", separator="|")
        self.assertIs(model.compile(inplace=True), model)
        self.assertIs(type(model), ConfiguredText)
        self.assertEqual(
            model.make_sentence_with_start("alpha beta", test_output=False),
            "alpha|beta|gamma",
        )
