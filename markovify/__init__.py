VERSION_TUPLE = (0, 2, 3)
VERSION = ".".join(map(str, VERSION_TUPLE))

from markovify.chain import Chain
from markovify.text import Text
from markovify.splitters import split_into_sentences
