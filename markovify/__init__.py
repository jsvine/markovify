VERSION_TUPLE = (0, 2, 5)
VERSION = ".".join(map(str, VERSION_TUPLE))

from .chain import Chain
from .text import Text
from .splitters import split_into_sentences
from .utils import combine
