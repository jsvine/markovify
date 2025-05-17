import functools
import re
import json
import random
from typing import (
    TYPE_CHECKING,
    Dict,
    Iterable,
    Iterator,
    List,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
)

if TYPE_CHECKING:
    from typing_extensions import TypedDict, Unpack

from .splitters import split_into_sentences
from .chain import Chain, BEGIN, State
from unidecode import unidecode


DEFAULT_MAX_OVERLAP_RATIO = 0.7
DEFAULT_MAX_OVERLAP_TOTAL = 15
DEFAULT_TRIES = 10


T = TypeVar("T")
TextT = TypeVar("TextT", bound="Text")


def cast_not_none(var: Union[T, None]) -> T:
    return cast(T, var)


if TYPE_CHECKING:

    class TextMarkovifyDict(TypedDict):
        state_size: int
        chain: str
        parsed_sentences: Union[List[List[str]], None]

    class MakeSentenceKwargs(TypedDict, total=False):
        tries: int
        max_overlap_ratio: float
        max_overlap_total: int
        test_output: bool
        max_words: Union[int, None]
        min_words: Union[int, None]


class ParamError(Exception):
    pass


class Text:
    reject_pat = re.compile(r"(^')|('$)|\s'|'\s|[\"(\(\)\[\])]")

    def __init__(
        self,
        input_text: Union[str, None],
        state_size: int = 2,
        chain: Union[Chain, None] = None,
        parsed_sentences: Union[List[List[str]], None] = None,
        retain_original: bool = True,
        well_formed: bool = True,
        reject_reg: "Union[str, re.Pattern]" = "",
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
        """

        self.well_formed = well_formed
        if well_formed and reject_reg != "":
            self.reject_pat = re.compile(reject_reg)

        can_make_sentences = parsed_sentences is not None or input_text is not None
        self.retain_original = retain_original and can_make_sentences
        self.state_size = state_size

        if self.retain_original:
            self.parsed_sentences = parsed_sentences or list(
                self.generate_corpus(cast_not_none(input_text))
            )

            # Rejoined text lets us assess the novelty of generated sentences
            self.rejoined_text = self.sentence_join(
                map(self.word_join, self.parsed_sentences)
            )
            self.chain = chain or Chain(self.parsed_sentences, state_size)
        else:
            if chain is None:
                if not can_make_sentences:
                    raise ParamError(
                        "Must provide either `input_text`, `parsed_sentences`, "
                        "or `chain`."
                    )
                parsed = parsed_sentences or self.generate_corpus(
                    cast_not_none(input_text)
                )
                self.chain = Chain(parsed, state_size)
            else:
                self.chain = chain

    def compile(self, inplace: bool = False) -> "Text":
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

    def to_dict(self) -> "TextMarkovifyDict":
        """
        Returns the underlying data as a Python dict.
        """
        return {
            "state_size": self.state_size,
            "chain": self.chain.to_json(),
            "parsed_sentences": self.parsed_sentences if self.retain_original else None,
        }

    def to_json(self) -> str:
        """
        Returns the underlying data as a JSON string.
        """
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls: Type[TextT], obj: "TextMarkovifyDict", **kwargs) -> TextT:
        return cls(
            None,
            state_size=obj["state_size"],
            chain=Chain.from_json(obj["chain"]),
            parsed_sentences=obj.get("parsed_sentences"),
        )

    @classmethod
    def from_json(cls: Type[TextT], json_str: str) -> TextT:
        return cls.from_dict(json.loads(json_str))

    def sentence_split(self, text: str) -> List[str]:
        """
        Splits full-text string into a list of sentences.
        """
        return split_into_sentences(text)

    def sentence_join(self, sentences: Iterable[str]) -> str:
        """
        Re-joins a list of sentences into the full text.
        """
        return " ".join(sentences)

    word_split_pattern = re.compile(r"\s+")

    def word_split(self, sentence: str) -> List[str]:
        """
        Splits a sentence into a list of words.
        """
        return re.split(self.word_split_pattern, sentence)

    def word_join(self, words: Iterable[str]) -> str:
        """
        Re-joins a list of words into a sentence.
        """
        return " ".join(words)

    def test_sentence_input(self, sentence: str) -> bool:
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

    def generate_corpus(self, text: str) -> Iterator[List[str]]:
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

    def test_sentence_output(
        self,
        words: List[str],
        max_overlap_ratio: float,
        max_overlap_total: int,
    ) -> bool:
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

    def make_sentence(
        self,
        init_state: Union[Tuple[str, ...], None] = None,
        **kwargs: "Unpack[MakeSentenceKwargs]",
    ) -> Union[str, None]:
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
        max_words = kwargs.get("max_words")
        min_words = kwargs.get("min_words")

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

    def make_short_sentence(
        self,
        max_chars: int,
        min_chars: int = 0,
        **kwargs: "Unpack[MakeSentenceKwargs]",
    ) -> Union[str, None]:
        """
        Tries making a sentence of no more than `max_chars` characters and optionally
        no less than `min_chars` characters, passing **kwargs to `self.make_sentence`.
        """
        tries = kwargs.get("tries", DEFAULT_TRIES)

        for _ in range(tries):
            sentence = self.make_sentence(**kwargs)
            if sentence and min_chars <= len(sentence) <= max_chars:
                return sentence

    def make_sentence_with_start(
        self,
        beginning: str,
        strict: bool = True,
        **kwargs: "Unpack[MakeSentenceKwargs]",
    ) -> str:
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
                init_states = self.find_init_states_from_chain(split)

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

    @functools.lru_cache(maxsize=1)
    def find_init_states_from_chain(self, split: State) -> List[State]:
        """
        Find all chains that begin with the split when `self.make_sentence_with_start`
        is called with strict == False.

        This is a very expensive operation, so lru_cache caches the results of
        the latest query in case `self.make_sentence_with_start` is called
        repeatedly with the same beginning string.
        """
        word_count = len(split)
        return [
            key
            for key in self.chain.model.keys()
            # check for starting with begin as well ordered lists
            if tuple(filter(lambda x: x != BEGIN, key))[:word_count] == split
        ]

    @classmethod
    def from_chain(
        cls: Type[TextT],
        chain_json: Union[str, Dict, List],
        corpus: Union[str, None] = None,
        parsed_sentences: Union[List[List[str]], None] = None,
    ) -> TextT:
        """
        Init a Text class based on an existing chain JSON string or object
        If corpus is None, overlap checking won't work.
        """
        chain = Chain.from_json(chain_json)
        return cls(
            corpus,
            parsed_sentences=parsed_sentences,
            state_size=chain.state_size,
            chain=chain,
        )


class NewlineText(Text):
    """
    A (usable) example of subclassing markovify.Text. This one lets you markovify
    text where the sentences are separated by newlines instead of ". "
    """

    def sentence_split(self, text: str) -> List[str]:
        return re.split(r"\s*\n\s*", text)
