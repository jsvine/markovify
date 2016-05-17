VERSION_TUPLE = (0, 3, 1)
VERSION = ".".join(map(str, VERSION_TUPLE))

from .chain import Chain
from .text import Text
from .splitters import split_into_sentences
from .utils import combine
