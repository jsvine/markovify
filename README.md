# Markovify

Markovify is a simple, extensible Markov chain generator. Right now, its main use is for building Markov models of large corpora of text, and generating random sentences from that. But, in theory, it could be used for [other applications](http://en.wikipedia.org/wiki/Markov_chain#Applications).

- [Why Markovify?](#why-markovify)
- [Installation](#installation)
- [Basic Usage](#basic-usage)
- [Advanced Usage](#advanced-usage)
- [Markovify In The Wild](#markovify-in-the-wild)
- [Thanks](#thanks)

## Why Markovify?

Some reasons:

- Simplicity. "Batteries included," but it's easy to override key methods.

- Models can be stored as JSON, allowing you to cache your results and save them for later.

- Text parsing and sentence generation methods are highly extensible, allowing you to set your own rules.

- Relies only on pure-Python libraries, and very few of them.

- Tested on Python 2.6, 2.7, 3.1, and 3.4.


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

- The usage examples here assume you're trying to markovify text. If you'd like to use the underlying `markovify.Chain` class, which is not text-specific, check out [the (annotated) source code](markovify/chain.py).

- Markovify works best with large, well-punctuated texts. If your text doesn't use `.`s to delineate sentences, put each sentence on a newline, and use the `markovify.NewlineText` class instead of `markovify.Text` class.

- If you've accidentally read your text as one long sentence, markovify will be unable to generate new sentences from it due to a lack of beginning and ending delimiters. This can happen if you've read a newline delimited file using the `markovify.Text` command instead of `markovify.NewlineText`. To check this, the command `[key for key in txt.chain.model.keys() if "___BEGIN__" in key]` command will return all of the possible sentence starting words, and should return more than one result.

- By default, the `make_sentence` method tries, a maximum of 10 times per invocation, to make a sentence that doesn't overlap too much with the original text. If it is successful, the method returns the sentence as a string. If not, it returns `None`. To increase or decrease the number of attempts, use the `tries` keyword argument, e.g., call `.make_sentence(tries=100)`.

- By default, `markovify.Text` tries to generate sentences that don't simply regurgitate chunks of the original text. The default rule is to suppress any generated sentences that exactly overlaps the original text by 15 words or 70% of the sentence's word count. You can change this rule by passing `max_overlap_ratio` and/or `max_overlap_total` to the `make_sentence` method.

## Advanced Usage

### Specifying the model's state size

By default, `markovify.Text` uses a state size of 2. But you can instantiate a model with a different state size. E.g.,:

```python
text_model = markovify.Text(text, state_size=3)
```

### Combining models

With `markovify.combine(...)`, you can combine two or more Markov chains. The function accepts two arguments:

- `models`: A list of `markovify` objects to combine. Can be instances of `markovify.Chain` or `markovify.Text` (or their subclasses), but all must be of the same type.
- `weights`: Optional. A list — the exact length of `models` — of ints or floats indicating how much relative emphasis to place on each source. Default: `[ 1, 1, ... ]`.

For instance:

```python
model_a = markovify.Text(text_a)
model_b = markovify.Text(text_b)

model_combo = markovify.combine([ model_a, model_b ], [ 1.5, 1 ])
```

... would combine `model_a` and `model_b`, but place 50% more weight on the connections from `model_a`.


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

### Exporting

It can take a while to generate a Markov model from a large corpus. Sometimes you'll want to generate once and reuse it later. To export a generated `markovify.Text` model, use `my_text_model.to_json()`. For example:

```python
corpus = open("sherlock.txt").read()

text_model = markovify.Text(corpus, state_size=3)
model_json = text_model.to_json()
# In theory, here you'd save the JSON to disk, and then read it back later.

reconstituted_model = markovify.Text.from_json(model_json)
reconstituted_model.make_short_sentence(140)

>>> 'It cost me something in foolscap, and I had no idea that he was a man of evil reputation among women.'
```

You can also export the underlying Markov chain on its own — i.e., excluding the original corpus and the `state_size` metadata — via `my_text_model.chain.to_json()`.

## Markovify In The Wild

- BuzzFeed's [Tom Friedman Sentence Generator](http://www.buzzfeed.com/jsvine/the-tom-friedman-sentence-generator) / [@mot_namdeirf](https://twitter.com/mot_namdeirf).
- [UserSim](https://github.com/trambelus/UserSim), which powers [/u/user_simulator](https://www.reddit.com/user/user_simulator) bot on Reddit and generates comments based on a user's comment history.
- [SubredditSimulator](https://www.reddit.com/r/SubredditSimulator), which generates random Reddit submissions and comments based on a subreddit's previous activity.
    - ["What is /r/SubredditSimulator?"](https://www.reddit.com/r/SubredditSimulator/comments/391ria/what_is_rsubredditsimulator/)
    - [Note re. `markovify`](https://www.reddit.com/r/SubredditSimMeta/comments/3d910r/i_was_inspired_by_this_place_and_made_a_twitter/ct3vjp0)
- [college crapplication](http://college-crapplication.appspot.com/), a web-app that generates college application essays. [[code](https://github.com/mattr555/college-crapplication)]
- [@MarkovPicard](https://twitter.com/MarkovPicard), a Twitter bot based on *Star Trek: The Next Generation* transcripts. [[code](https://github.com/rdsheppard95/MarkovPicard)]
- [sekrits.herokuapp.com](https://sekrits.herokuapp.com/), a `markovify`-powered quiz that challenges you to tell the difference between "two file titles relating to matters of [Australian] national security" — one real and one fake. [[code](https://sekrits.herokuapp.com/)]
- [Hacker News Simulator](http://news.ycombniator.com/), which does what it says on the tin. [[code](https://github.com/orf/hnewssimulator)]
- [Stak Attak](http://www.stakattak.me/), a "poetic stackoverflow answer generator." [[code](https://github.com/theannielin/hackharvard)]
- [MashBOT](https://twitter.com/mashomatic), a `markovify`-powered Twitter bot attached to a printer. Presented by [Helen J Burgess at Babel Toronto 2015](http://electric.press/mash/). [[code](https://github.com/hyperrhiz/mashbot)]
- [The Mansfield Reporter](http://maxlupo.com/mansfield-reporter/), "a simple device which can generate new text from some of history's greatest authors [...] running on a tiny Raspberry Pi, displaying through a tft screen from Adafruit." 
- [twitter markov](https://github.com/fitnr/twitter_markov), a tool to "create markov chain ("_ebooks") accounts on Twitter."
- [@Bern_Trump_Bot](https://twitter.com/bern_trump_bot), "Bernie Sanders and Donald Trump driven by Markov Chains." [[code](https://github.com/MichaelMartinez/Bern_Trump_Bot)]
- [@RealTrumpTalk](https://twitter.com/RealTrumpTalk), "A bot that uses the things that @realDonaldTrump tweets to create it's own tweets." [[code](https://github.com/CastleCorp/TrumpTalk)]
- [Taylor Swift Song Generator](http://taytay.mlavin.org/), which does what it says. [[code](https://github.com/caktus/taytay)]
- [@BOTtalks](https://twitter.com/bottalks) / [ideasworthautomating.com](http://ideasworthautomating.com/). "TIM generates talks on a broad spectrum of topics, based on the texts of slightly more coherent talks given under the auspices of his more famous big brother, who shall not be named here." [[code](https://github.com/alexislloyd/tedbot)]
- [Internal Security Zones](http://rebecca-ricks.com/2016/05/06/internal-security-zones/), "Generative instructions for prison design & maintenance." [[code](https://github.com/baricks/internal-security-zones)]
- [Miraculous Ladybot](http://miraculousladybot.tumblr.com/). Generates [Miraculous Ladybug](https://en.wikipedia.org/wiki/Miraculous:_Tales_of_Ladybug_%26_Cat_Noir) fanfictions and posts them on Tumblr. [[code](https://github.com/veggiedefender/miraculousladybot)]
- [@HaikuBotto](https://twitter.com/HaikuBotto), "I'm a bot that writes haiku from literature. beep boop" [[code](https://github.com/balysv/HaikuBotto)]
- [Chat Simulator Bot](http://www.telegram.me/ChatSimulatorBot), a bot for Telegram. [[code](https://github.com/GuyAglionby/chatsimulatorbot)]
- [emojipasta.club](http://emojipasta.club), "a web service that exposes RESTful endpoints for generating emojipastas, as well as a simple frontend for generating and tweeting emojipasta sentences." [[code](https://github.com/ntratcliff/emojipasta.club)]
- [Towel Generator](http://towel.labs.wasv.me/), "A system for generating sentences similar to those from the hitchhikers series of books." [[code](https://github.com/wastevensv/towelday)]
- [@mercurialbot](https://twitter.com/mercurialbot), "A twitter bot that generates tweets based on its mood." [[code](https://github.com/brahmcapoor/Mercury)]
- [becomeacurator.com](http://becomeacurator.com/), which "generates curatorial statements for contemporary art expositions, using Markov chains and texts from galleries around the world." [[code](https://github.com/jjcastro/markov-curatorial-generator)]
- [mannynotfound/interview-bot](https://github.com/mannynotfound/interview-bot), "A python based terminal prompt app to automate the interview process."
- [Steam Game Generator](http://applepinegames.com/tech/steam-game-generator), which "uses data from real Steam games, randomized using Markov chains." [[code](https://github.com/applepinegames/steam_game_generator)]
- [@DicedOnionBot](https://twitter.com/DicedOnionBot), which "generates new headlines by The Onion by regurgitating and combining old headlines." [[code](https://github.com/mobeets/fake-onion)]
- [@thought__leader](https://twitter.com/thought__leader), "Thinking thoughts so you don't have to!" [[blog post](http://jordan-wright.com/blog/post/2016-04-08-i-automated-infosec-thought-leadership/)]
- [@_murakamibot](https://twitter.com/_murakamibot) and [@jamesjoycebot](https://twitter.com/jamesjoycebot), bots that tweet Haruki Murakami and James Joyce-like sentences. [[code](https://github.com/tmkuba/markovBot)]
- [shartificialintelligence.com](http://www.shartificialintelligence.com/), "the world's first creative ad agency staffed entirely with copywriter robots." [[code](https://github.com/LesGuessing/shartificial-intelligence)]
- [@NightValeFeed](https://twitter.com/NightValeFeed), which "generates tweets by combining [@NightValeRadio](https://twitter.com/NightValeRadio) tweets with [@BuzzFeed](https://twitter.com/BuzzFeed) headlines." [[code](https://github.com/stepjue/night-vale-buzzfeed)]

Have other examples? Pull requests welcome.

## Thanks

Many thanks to the following GitHub users for contributing code and/or ideas:

- [@orf](https://github.com/orf)
- [@deimos](https://github.com/deimos)
- [@cjmochrie](https://github.com/cjmochrie)
- [@Jaza](https://github.com/Jaza)
- [@fitnr](https://github.com/fitnr)
- [@andela-mfalade](https://github.com/andela-mfalade)
- [@ntratcliff](https://github.com/ntratcliff)
- [@schollz](https://github.com/schollz)
- [@aalireza](https://github.com/aalireza)
- [@bfontaine](https://github.com/bfontaine)
- [@tmsherman](https://github.com/tmsherman)
- [@wodim](https://github.com/wodim)
- [@eh11fx](https://github.com/eh11fx)
- [@ammgws](https://github.com/ammgws)

Developed at [BuzzFeed](https://www.buzzfeed.com).
