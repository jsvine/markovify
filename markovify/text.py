import re
import json
import multiprocessing as mp
import os
import random
from .splitters import split_into_sentences
from .chain import Chain, BEGIN
from unidecode import unidecode

DEFAULT_MAX_OVERLAP_RATIO = 0.7
DEFAULT_MAX_OVERLAP_TOTAL = 15
DEFAULT_TRIES = 10


class ParamError(Exception):
    pass


class Text:

    reject_pat = re.compile(r"(^')|('$)|\s'|'\s|[\"(\(\)\[\])]")

    def __init__(
        self,
        input_text,
        state_size=2,
        chain=None,
        parsed_sentences=None,
        retain_original=True,
        well_formed=True,
        reject_reg="",
        multiprocess=False,
        multiprocess_workers=len(os.sched_getaffinity(0)),
    ):
        """
        input_text: A string.
        state_size: An integer, indicating the number of words in the model's state.
        chain: A trained markovify.Chain instance for this text, if pre-processed.
        parsed_sentences: A list of lists, where each outer list is a "run"
              of the process (e.g. a single sentence), and each inner list
              contains the steps (e.g. words) in the run. If you want to simulate
              an infinite process, you can come very close by passing just one, very
              long run.
        retain_original: Indicates whether to keep the original corpus.
        well_formed: Indicates whether sentences should be well-formed, preventing
              unmatched quotes, parenthesis by default, or a custom regular expression
              can be provided.
        reject_reg: If well_formed is True, this can be provided to override the
              standard rejection pattern.
        multiprocess: Indicates whether to generate model using multiprocessing.
        multiprocess_workers: An integer, indicating the number of multiprocess
              workers. Defaults to the number of usable CPUs.
        """

        self.well_formed = well_formed
        if well_formed and reject_reg != "":
            self.reject_pat = re.compile(reject_reg)

        can_make_sentences = parsed_sentences is not None or input_text is not None
        self.retain_original = retain_original and can_make_sentences
        self.state_size = state_size

        if multiprocess:
            generate_corpus = self.mp_generate_corpus
            self.multiprocess_workers = multiprocess_workers
        else:
            generate_corpus = self.generate_corpus

        if self.retain_original:
            self.parsed_sentences = parsed_sentences or list(
                generate_corpus(input_text)
            )

            # Rejoined text lets us assess the novelty of generated sentences
            self.rejoined_text = self.sentence_join(
                map(self.word_join, self.parsed_sentences)
            )
            self.chain = chain or Chain(self.parsed_sentences, state_size)
        else:
            if not chain:
                parsed = parsed_sentences or generate_corpus(input_text)
            self.chain = chain or Chain(parsed, state_size)

    def compile(self, inplace=False):
        if inplace:
            self.chain.compile(inplace=True)
            return self
        cchain = self.chain.compile(inplace=False)
        psent = None
        if hasattr(self, "parsed_sentences"):
            psent = self.parsed_sentences
        return Text(
            None,
            state_size=self.state_size,
            chain=cchain,
            parsed_sentences=psent,
            retain_original=self.retain_original,
            well_formed=self.well_formed,
            reject_reg=self.reject_pat,
        )

    def to_dict(self):
        """
        Returns the underlying data as a Python dict.
        """
        return {
            "state_size": self.state_size,
            "chain": self.chain.to_json(),
            "parsed_sentences": self.parsed_sentences if self.retain_original else None,
        }

    def to_json(self):
        """
        Returns the underlying data as a JSON string.
        """
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, obj, **kwargs):
        return cls(
            None,
            state_size=obj["state_size"],
            chain=Chain.from_json(obj["chain"]),
            parsed_sentences=obj.get("parsed_sentences"),
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
        A basic sentence filter. The default rejects sentences that contain
        the type of punctuation that would look strange on its own
        in a randomly-generated sentence.
        """
        if len(sentence.strip()) == 0:
            return False
        # Decode unicode, mainly to normalize fancy quotation marks
        decoded = unidecode(sentence)
        # Sentence shouldn't contain problematic characters
        if self.well_formed and self.reject_pat.search(decoded):
            return False
        return True

    def generate_corpus(self, text):
        """
        Given a text string, returns a list of lists; that is, a list of
        "sentences," each of which is a list of words. Before splitting into
        words, the sentences are filtered through `self.test_sentence_input`
        """
        if isinstance(text, str):
            sentences = self.sentence_split(text)
        else:
            sentences = []
            for line in text:
                sentences += self.sentence_split(line)
        passing = filter(self.test_sentence_input, sentences)
        runs = map(self.word_split, passing)
        return runs

    def mp_generate_corpus(self, text):
        """
        Given a text string, returns a list of lists; that is, a list of
        "sentences," each of which is a list of words. Before splitting into
        words, the sentences are filtered through `self.test_sentence_input`
        """

        # TODO: find something which cannot be present in input
        END = "KTHXBYE"

        # mp workers implementation. They work on (multi-)producer,
        # (multi-)consumer queues delegating to user-defined logic
        # the actual work.

        def test_sentence_input_worker(sentences, passing):
            for sentence in iter(sentences.get, END):
                if self.test_sentence_input(sentence):
                    passing.put(sentence)
            passing.put(END)

        def word_split_worker(passing, splitted):
            for sentence in iter(passing.get, END):
                splitted.put(self.word_split(sentence))
            splitted.put(END)

        # create pool containers and queues
        test_sentence_input_worker_pool = []
        word_split_worker_pool = []

        sentences = mp.Queue()
        passing = mp.Queue()
        splitted = mp.Queue()

        # spawn + start workers
        for _ in range(self.multiprocess_workers):
            test_sentence_input_worker_process = mp.Process(
                target=test_sentence_input_worker,
                args=(sentences, passing),
            )
            test_sentence_input_worker_process.start()
            test_sentence_input_worker_pool.append(test_sentence_input_worker_process)

            word_split_worker_process = mp.Process(
                target=word_split_worker,
                args=(passing, splitted),
            )
            word_split_worker_process.start()
            word_split_worker_pool.append(word_split_worker_process)

        # feed sentences queue with our input + sentinels
        if isinstance(text, str):
            for sentence in self.sentence_split(text):
                sentences.put(sentence)
        else:
            for line in text:
                for sentence in self.sentence_split(line):
                    sentences.put(sentence)

        for _ in range(self.multiprocess_workers):
            sentences.put(END)

        # consume output queue, expecting for self.multiprocess_workers sentinels
        runs = []
        for _ in range(self.multiprocess_workers):
            for item in iter(splitted.get, END):
                runs.append(item)

        # join the two pools
        for process in test_sentence_input_worker_pool:
            process.join()

        for process in word_split_worker_pool:
            process.join()

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
        overlap_ratio = round(max_overlap_ratio * len(words))
        overlap_max = min(max_overlap_total, overlap_ratio)
        overlap_over = overlap_max + 1
        gram_count = max((len(words) - overlap_max), 1)
        grams = [words[i : i + overlap_over] for i in range(gram_count)]
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

        If `max_words` or `min_words` are specified, the word count for the
        sentence will be evaluated against the provided limit(s).
        """
        tries = kwargs.get("tries", DEFAULT_TRIES)
        mor = kwargs.get("max_overlap_ratio", DEFAULT_MAX_OVERLAP_RATIO)
        mot = kwargs.get("max_overlap_total", DEFAULT_MAX_OVERLAP_TOTAL)
        test_output = kwargs.get("test_output", True)
        max_words = kwargs.get("max_words", None)
        min_words = kwargs.get("min_words", None)

        if init_state is None:
            prefix = []
        else:
            prefix = list(init_state)
            for word in prefix:
                if word == BEGIN:
                    prefix = prefix[1:]
                else:
                    break

        for _ in range(tries):
            words = prefix + self.chain.walk(init_state)
            if (max_words is not None and len(words) > max_words) or (
                min_words is not None and len(words) < min_words
            ):
                continue  # pragma: no cover # see coveragepy/issues/198
            if test_output and hasattr(self, "rejoined_text"):
                if self.test_sentence_output(words, mor, mot):
                    return self.word_join(words)
            else:
                return self.word_join(words)
        return None

    def make_short_sentence(self, max_chars, min_chars=0, **kwargs):
        """
        Tries making a sentence of no more than `max_chars` characters and optionally
        no less than `min_chars` characters, passing **kwargs to `self.make_sentence`.
        """
        tries = kwargs.get("tries", DEFAULT_TRIES)

        for _ in range(tries):
            sentence = self.make_sentence(**kwargs)
            if sentence and min_chars <= len(sentence) <= max_chars:
                return sentence

    def make_sentence_with_start(self, beginning, strict=True, **kwargs):
        """
        Tries making a sentence that begins with `beginning` string,
        which should be a string of one to `self.state` words known
        to exist in the corpus.

        If strict == True, then markovify will draw its initial inspiration
        only from sentences that start with the specified word/phrase.

        If strict == False, then markovify will draw its initial inspiration
        from any sentence containing the specified word/phrase.

        **kwargs are passed to `self.make_sentence`
        """
        split = tuple(self.word_split(beginning))
        word_count = len(split)

        if word_count == self.state_size:
            init_states = [split]

        elif 0 < word_count < self.state_size:
            if strict:
                init_states = [(BEGIN,) * (self.state_size - word_count) + split]

            else:
                init_states = [
                    key
                    for key in self.chain.model.keys()
                    # check for starting with begin as well ordered lists
                    if tuple(filter(lambda x: x != BEGIN, key))[:word_count] == split
                ]

                random.shuffle(init_states)
        else:
            err_msg = (
                f"`make_sentence_with_start` for this model requires a string "
                f"containing 1 to {self.state_size} words. "
                f"Yours has {word_count}: {str(split)}"
            )
            raise ParamError(err_msg)

        for init_state in init_states:
            output = self.make_sentence(init_state, **kwargs)
            if output is not None:
                return output
        err_msg = (
            f"`make_sentence_with_start` can't find sentence beginning with {beginning}"
        )
        raise ParamError(err_msg)

    @classmethod
    def from_chain(cls, chain_json, corpus=None, parsed_sentences=None):
        """
        Init a Text class based on an existing chain JSON string or object
        If corpus is None, overlap checking won't work.
        """
        chain = Chain.from_json(chain_json)
        return cls(
            corpus or None,
            parsed_sentences=parsed_sentences,
            state_size=chain.state_size,
            chain=chain,
        )


class NewlineText(Text):
    """
    A (usable) example of subclassing markovify.Text. This one lets you markovify
    text where the sentences are separated by newlines instead of ". "
    """

    def sentence_split(self, text):
        return re.split(r"\s*\n\s*", text)
