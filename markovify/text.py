import re
import json
from .splitters import split_into_sentences
from .chain import Chain, BEGIN, END
from unidecode import unidecode

DEFAULT_MAX_OVERLAP_RATIO = 0.7
DEFAULT_MAX_OVERLAP_TOTAL = 15
DEFAULT_TRIES = 10

class ParamError(Exception):
    pass

class Text(object):

    def __init__(self, input_text, state_size=2, chain=None, parsed_sentences=None):
        """
        input_text: A string.
        state_size: An integer, indicating the number of words in the model's state.
        chain: A trained markovify.Chain instance for this text, if pre-processed.
        parsed_sentences: A list of lists, where each outer list is a "run"
              of the process (e.g. a single sentence), and each inner list
              contains the steps (e.g. words) in the run. If you want to simulate
              an infinite process, you can come very close by passing just one, very
              long run.
        """
        self.state_size = state_size
        self.parsed_sentences = parsed_sentences or list(self.generate_corpus(input_text))

        # Rejoined text lets us assess the novelty of generated sentences
        self.rejoined_text = self.sentence_join(map(self.word_join, self.parsed_sentences))
        self.chain = chain or Chain(self.parsed_sentences, state_size)

    def to_dict(self):
        """
        Returns the underlying data as a Python dict.
        """
        return {
            "state_size": self.state_size,
            "chain": self.chain.to_json(),
            "parsed_sentences": self.parsed_sentences
        }

    def to_json(self):
        """
        Returns the underlying data as a JSON string.
        """
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, obj):
        return cls(
            None,
            state_size=obj["state_size"],
            chain=Chain.from_json(obj["chain"]),
            parsed_sentences=obj["parsed_sentences"]
        )

    @classmethod
    def from_json(cls, json_str):
        return cls.from_dict(json.loads(json_str))

    def sentence_split(self, text):
        """
        Splits full-text string into a list of sentences.
        """
        return split_into_sentences(text)

    def sentence_join(self, sentences):
        """
        Re-joins a list of sentences into the full text.
        """
        return " ".join(sentences)

    word_split_pattern = re.compile(r"\s+")
    def word_split(self, sentence):
        """
        Splits a sentence into a list of words.
        """
        return re.split(self.word_split_pattern, sentence)

    def word_join(self, words):
        """
        Re-joins a list of words into a sentence.
        """
        return " ".join(words)

    def test_sentence_input(self, sentence):
        """
        A basic sentence filter. This one rejects sentences that contain
        the type of punctuation that would look strange on its own
        in a randomly-generated sentence.
        """
        reject_pat = re.compile(r"(^')|('$)|\s'|'\s|[\"(\(\)\[\])]")
        # Decode unicode, mainly to normalize fancy quotation marks
        if sentence.__class__.__name__ == "str": # pragma: no cover
            decoded = sentence
        else: # pragma: no cover
            decoded = unidecode(sentence)
        # Sentence shouldn't contain problematic characters
        if re.search(reject_pat, decoded): return False
        return True

    def generate_corpus(self, text):
        """
        Given a text string, returns a list of lists; that is, a list of
        "sentences," each of which is a list of words. Before splitting into
        words, the sentences are filtered through `self.test_sentence_input`
        """
        sentences = self.sentence_split(text)
        passing = filter(self.test_sentence_input, sentences)
        runs = map(self.word_split, passing)
        return runs

    def test_sentence_output(self, words, max_overlap_ratio, max_overlap_total):
        """
        Given a generated list of words, accept or reject it. This one rejects
        sentences that too closely match the original text, namely those that
        contain any identical sequence of words of X length, where X is the
        smaller number of (a) `max_overlap_ratio` (default: 0.7) of the total
        number of words, and (b) `max_overlap_total` (default: 15).
        """
        # Reject large chunks of similarity
        overlap_ratio = int(round(max_overlap_ratio * len(words)))
        overlap_max = min(max_overlap_total, overlap_ratio)
        overlap_over = overlap_max + 1
        gram_count = max((len(words) - overlap_max), 1)
        grams = [ words[i:i+overlap_over] for i in range(gram_count) ]
        for g in grams:
            gram_joined = self.word_join(g)
            if gram_joined in self.rejoined_text:
                return False
        return True

    def make_sentence(self, init_state=None, **kwargs):
        """
        Attempts `tries` (default: 10) times to generate a valid sentence,
        based on the model and `test_sentence_output`. Passes `max_overlap_ratio`
        and `max_overlap_total` to `test_sentence_output`.

        If successful, returns the sentence as a string. If not, returns None.

        If `init_state` (a tuple of `self.chain.state_size` words) is not specified,
        this method chooses a sentence-start at random, in accordance with
        the model.
        
        If `test_output` is set as False then the `test_sentence_output` check
        will be skipped.
        
        If `max_words` is specified, the word count for the sentence will be
        evaluated against the provided limit.
        """
        tries = kwargs.get('tries', DEFAULT_TRIES)
        mor = kwargs.get('max_overlap_ratio', DEFAULT_MAX_OVERLAP_RATIO)
        mot = kwargs.get('max_overlap_total', DEFAULT_MAX_OVERLAP_TOTAL)
        test_output = kwargs.get('test_output', True)
        max_words = kwargs.get('max_words', None)

        for _ in range(tries):
            if init_state != None:
                if init_state[0] == BEGIN:
                    prefix = list(init_state[1:])
                else:
                    prefix = list(init_state)
            else:
                prefix = []
            words = prefix + self.chain.walk(init_state)
            if max_words != None and len(words) > max_words:
                continue
            if test_output:
                if self.test_sentence_output(words, mor, mot):
                    return self.word_join(words)
            else:
                return self.word_join(words)
        return None

    def make_short_sentence(self, max_chars, min_chars=0, **kwargs):
        """
        Tries making a sentence of no more than `max_chars` characters and optionally
        no less than `min_chars` charcaters, passing **kwargs to `self.make_sentence`.
        """
        tries = kwargs.get('tries', DEFAULT_TRIES)

        for _ in range(tries):
            sentence = self.make_sentence(**kwargs)
            if sentence and len(sentence) <= max_chars and len(sentence) >= min_chars:
                return sentence

    def make_sentence_with_start(self, beginning, **kwargs):
        """
        Tries making a sentence that begins with `beginning` string,
        which should be a string of one or two words known to exist in the
        corpus. **kwargs are passed to `self.make_sentence`.
        """
        split = self.word_split(beginning)
        word_count = len(split)
        if word_count == self.state_size:
            init_state = tuple(split)
        elif word_count > 0 and word_count < self.state_size:
            init_state = tuple([ BEGIN ] * (self.state_size - word_count) + split)
        else:
            err_msg = "`make_sentence_with_start` for this model requires a string containing 1 to {0} words. Yours has {1}: {2}".format(self.state_size, word_count, str(split))
            raise ParamError(err_msg)

        return self.make_sentence(init_state, **kwargs)

    def make_sentence_with_starting_letter(self, letter, **kwargs):
        """
        Tries to make a sentence whose first word starts with letter `letter`.
        """
        first_word = None
        while first_word is None:
            candidates = list(self.chain.gen())
            try:
                first_word = filter(lambda word: word[0] in [letter.upper(), letter.lower()],
                                    candidates[:len(candidates) - 1])[0]
                second_word = candidates[candidates.index(first_word) + 1]
            except IndexError:
                pass
        return self.make_sentence((first_word, second_word), **kwargs)

    @classmethod
    def from_chain(cls, chain_json, corpus=None, parsed_sentences=None):
        """
        Init a Text class based on an existing chain JSON string or object
        If corpus is None, overlap checking won't work.
        """
        chain = Chain.from_json(chain_json)
        return cls(corpus or '', parsed_sentences=parsed_sentences, state_size=chain.state_size, chain=chain)


class NewlineText(Text):
    """
    A (usable) example of subclassing markovify.Text. This one lets you markovify
    text where the sentences are separated by newlines instead of ". "
    """
    def sentence_split(self, text):
        return re.split(r"\s*\n\s*", text)
