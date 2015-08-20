import re
import string
import markovify
from unidecode import unidecode

class Text(object):
    def __init__(self, input_text, state_size=2, chain=None):
        """
        input_text: A string.
        state_size: An integer, indicating the number of words in the model's state.
        chain: A trained markovify.Chain instance for this text, if pre-processed.
        """
        runs = list(self.generate_corpus(input_text))
        # Rejoined text lets us assess the novelty of generated sentences
        self.rejoined_text = self.sentence_join(map(self.word_join, runs))
        self.state_size = state_size        
        self.chain = chain or markovify.Chain(runs, state_size)

    def sentence_split(self, text):
        """
        Splits full-text string into a list of sentences.
        """
        return markovify.split_into_sentences(text)

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
        if sentence.__class__.__name__ == "str":
            decoded = sentence
        else:
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

    def test_sentence_output(self, words, max_overlap_ratio, max_overlap_cap):
        """
        Given a generated list of words, accept or reject it. This one rejects
        sentences that too closely match the original text, namely those that
        contain any identical sequence of words of X length, where X is the
        smaller number of (a) max_overlap_ratio of the total number of words,
        and (b) max_overlap_cap.
        """
        # Reject large chunks of similarity
        overlap_ratio = int(round(max_overlap_ratio * len(words)))
        overlap_max = min(max_overlap_cap, overlap_ratio)
        overlap_over = overlap_max + 1
        gram_count = max((len(words) - overlap_max), 1)
        grams = [ words[i:i+overlap_over] for i in range(gram_count) ]
        for g in grams:
            gram_joined = self.word_join(g)
            if gram_joined in self.rejoined_text:
                return False
        return True
            
    def make_sentence(self, init_state=None, tries=10, max_overlap_ratio=0.7, max_overlap_cap=15):
        """
        Attempts `tries` (default: 10) times to generate a valid sentence,
        based on the model and self.test_sentence_output.

        max_overlap_ratio and max_overlap_cap set the rejection frequency of test_sentence output.

        If successful, returns the sentence as a string. If not, returns None.

        If `init_state` (a tuple of `self.state_size` words) is not specified,
        this method chooses a sentence-start at random, in accordance with the model.
        """
        for i in range(tries):
            words = self.chain.walk(init_state)
            if self.test_sentence_output(words, max_overlap_ratio, max_overlap_cap):
                return self.word_join(words)
            else:
                continue
        return None
    
    def make_short_sentence(self, char_limit, **kwargs):
        """
        Tries making a sentence of no more than `char_limit` characters`,
        passing **kwargs to self.make_sentence.
        """
        while True:
            sentence = self.make_sentence(**kwargs)
            if sentence and len(sentence) < char_limit:
                return sentence

    def make_prompt_sentence(self, prompt_word, **kwargs):
        """
        Tries making a sentence that contains the prompt word,
        passing **kwargs to self.make_sentence
        Tries 50 times by default.
        """
        for i in range(50):
            sentence = self.make_sentence(**kwargs)
            if prompt_word.lower() in sentence.lower():
                return sentence
        return None

class NewlineText(Text):
    """
    A (usable) example of subclassing markovify.Text. This one lets you markovify
    text where the sentences are separated by newlines instead of ". "
    """
    def sentence_split(self, text):
        return re.split(r"\s*\n\s*", text)
