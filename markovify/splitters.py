import re

uppercase_letter_pat = re.compile(r"^[A-Z]$", re.UNICODE)
initialism_pat = re.compile(r"^[A-Za-z0-9]{1,2}(\.[A-Za-z0-9]{1,2})+\.$", re.UNICODE)

# States w/ with thanks to https://github.com/unitedstates/python-us
# Titles w/ thanks to https://github.com/nytimes/emphasis and @donohoe
abbr_capped = "|".join(
    [
        "ala|ariz|ark|calif|colo|conn|del|fla|ga|ill|ind",  # States
        "kan|ky|la|md|mass|mich|minn|miss|mo|mont",  # States
        "neb|nev|okla|ore|pa|tenn|vt|va|wash|wis|wyo",  # States
        "u.s",
        "mr|ms|mrs|msr|dr|gov|pres|sen|sens|rep|reps",  # Titles
        "prof|gen|messrs|col|sr|jf|sgt|mgr|fr|rev",  # Titles
        "jr|snr|atty|supt",  # Titles
        "ave|blvd|st|rd|hwy",  # Streets
        "jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec",  # Months
    ]
).split("|")

abbr_lowercase = "etc|v|vs|viz|al|pct".split("|")


def is_abbreviation(dotted_word):
    clipped = dotted_word[:-1]
    if re.match(uppercase_letter_pat, clipped[0]):
        if len(clipped) == 1:  # Initial
            return True
        elif clipped.lower() in abbr_capped:
            return True
        else:
            return False
    else:
        if clipped in abbr_lowercase:
            return True
        else:
            return False


def is_sentence_ender(word):
    if re.match(initialism_pat, word) is not None:
        return False
    if word[-1] in ["?", "!"]:
        return True
    if len(re.sub(r"[^A-Z]", "", word)) > 1:
        return True
    if word[-1] == "." and (not is_abbreviation(word)):
        return True
    return False


def split_into_sentences(text):
    potential_end_pat = re.compile(
        r"".join(
            [
                r"([\w\.'’&\]\)]+[\.\?!])",  # A word that ends with punctuation
                r"([‘’“”'\"\)\]]*)",  # Followed by optional quote/parens/etc
                r"(\s+(?![a-z\-–—]))",  # Followed by whitespace + non-(lowercase/dash)
            ]
        ),
        re.U,
    )
    dot_iter = re.finditer(potential_end_pat, text)
    end_indices = [
        (x.start() + len(x.group(1)) + len(x.group(2)))
        for x in dot_iter
        if is_sentence_ender(x.group(1))
    ]
    spans = zip([None] + end_indices, end_indices + [None])
    sentences = [text[start:end].strip() for start, end in spans]
    return sentences
