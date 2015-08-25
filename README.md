# Markovify

Markovify is a simple, extensible Markov chain generator. Right now, its main use is for building Markov models of large corpora of text, and generating random sentences from that. But, in theory, it could be used for [other applications](http://en.wikipedia.org/wiki/Markov_chain#Applications).

Some features include:

- Simplicity. "Batteries included," but it's easy to override key methods.

- Models can be stored as JSON, allowing you to cache your results and save them for later.

- Text parsing and sentence generation methods are highly extensible, allowing you to set your own rules.

- Relies only on pure-Python libraries, and very few of them.

Developed at [BuzzFeed](http://www.buzzfeed.com/).

## Installation

```
pip install markovify
```

## Basic Usage

```python
import markovify

# Get raw text as string.
with open("/path/to/my/corpus.txt") as f:
    text = f.read()

# Build the model.
text_model = markovify.Text(text)

# Print five randomly-generated sentences
for i in range(5):
    print(text_model.make_sentence())

# Print three randomly-generated sentences of no more than 140 characters
for i in range(3):
    print(text_model.make_short_sentence(140))
```

Notes:

- The usage examples here assume you're trying to markovify text. If you'd like to use the underlying `markovify.Chain` class, which is not text-specific, check out [the (annotated) source code](markovify/model.py).

- Markovify works best with large, well-punctuated texts. If your text doesn't use `.`s to delineate sentences, put each sentence on a newline, and use the `markovify.NewlineText` class instead of `markovify.Text` class.

- By default, the `make_sentence` method tries, a maximum of 10 times per invocation, to make a sentence that doesn't overlap too much with the original text. If it is successful, the method returns the sentence as a string. If not, it returns `None`. To increase or decrease the number of attempts, use the `tries` keyword argument, e.g., call `.make_sentence(tries=100)`.

- By default, `markovify.Text` tries to generate sentences that don't simply regurgitate chunks of the original text. The default rule is to suppress any generated sentences that exactly overlaps the original text by 15 words or 70% of the sentence's word count. You can change this rule by passing `max_overlap_ratio` and/or `max_overlap_total` to the `make_sentence` method.

## Advanced Usage

### Specifying the model's state size

By default, `markovify.Text` uses a state size of 2. But you can instantiate a model with a different state size. E.g.,:

```python
text_model = markovify.Text(text, state_size=3)
```

### Extending `markovify.Text`

The `markovify.Text` class is highly extensible; most methods can be overridden. For example, the following `POSifiedText` class uses NLTK's part-of-speech tagger to generate a Markov model that obeys sentence structure better than a naive model. (It works. But be warned: `pos_tag` is very slow.)

```python
import markovify
import nltk
import re

class POSifiedText(markovify.Text):
    def word_split(self, sentence):
        words = re.split(self.word_split_pattern, sentence)
        words = [ "::".join(tag) for tag in nltk.pos_tag(words) ]
        return words

    def word_join(self, words):
        sentence = " ".join(word.split("::")[0] for word in words)
        return sentence
```

The most useful `markovify.Text` models you can override are:

- `sentence_split`
- `sentence_join`
- `word_split`
- `word_join`
- `test_sentence_input`
- `test_sentence_output`

For details on what they do, see [the (annotated) source code](markovify/text.py).

## Markovify In The Wild

- BuzzFeed's [Tom Friedman Sentence Generator](http://www.buzzfeed.com/jsvine/the-tom-friedman-sentence-generator) / [@mot_namdeirf](https://twitter.com/mot_namdeirf).
- [UserSim](https://github.com/trambelus/UserSim), which powers [/u/user_simulator](https://www.reddit.com/user/user_simulator) bot on Reddit and generates comments based on a user's comment history.
- [SubredditSimulator](https://www.reddit.com/r/SubredditSimulator), which generates random Reddit submissions and comments based on a subreddit's previous activity.
    - ["What is /r/SubredditSimulator?"](https://www.reddit.com/r/SubredditSimulator/comments/391ria/what_is_rsubredditsimulator/)
    - [Note re. `markovify`](https://www.reddit.com/r/SubredditSimMeta/comments/3d910r/i_was_inspired_by_this_place_and_made_a_twitter/ct3vjp0)
- [college crapplication](http://college-crapplication.appspot.com/), a web-app that generates college application essays. [[code](https://github.com/mattr555/college-crapplication)]
- [@MarkovPicard](https://twitter.com/MarkovPicard), a Twitter bot based on *Star Trek: The Next Generation* transcripts. [[code](https://github.com/rdsheppard95/MarkovPicard)]
- [sekrits.herokuapp.com](https://sekrits.herokuapp.com/), a `markovify`-powered quiz that challenges you to tell the difference between "two file titles relating to matters of [Australian] national security" — one real and one fake. [[code](https://sekrits.herokuapp.com/)]

Have other examples? Pull requests welcome.
