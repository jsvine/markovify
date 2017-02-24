# -*- coding: utf-8 -*-
import re

ascii_lowercase = "abcdefghijklmnopqrstuvwxyz"
ascii_uppercase = ascii_lowercase.upper()

# States w/ with thanks to https://github.com/unitedstates/python-us
# Titles w/ thanks to https://github.com/nytimes/emphasis and @donohoe
abbr_capped = "|".join([
    (
        "ala|ariz|ark|calif|colo|conn|del|fla|ga|ill|ind|kan|ky|la|md|mass|"
        "mich|minn|miss|mo|mont|neb|nev|okla|ore|pa|tenn|vt|va|wash|wis|wyo"
    ),  # States
    (
        "u.s"
    ),
    (
        "mr|ms|mrs|msr|dr|gov|pres|sen|sens|rep|reps|prof|gen|messrs|col|sr|jf|"
        "sgt|mgr|fr|rev|jr|snr|atty|supt"
    ),  # Titles
    (
        "ave|blvd|st|rd|hwy"
    ),  # Streets
    (
        "jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec"
    ),  # Months
    "|".join(ascii_lowercase)  # Initials
]).split("|")

abbr_lowercase = "etc|v|vs|viz|al|pct"

exceptions = "U.S.|U.N.|E.U.|F.B.I.|C.I.A.".split("|")


def is_abbreviation(dotted_word):
    clipped = dotted_word[:-1]
    if clipped[0] in ascii_uppercase:
        return clipped.lower() in abbr_capped
    else:
        return clipped in abbr_lowercase


def is_sentence_ender(word):
    if word in exceptions:
        return False
    if word[-1] in ["?", "!"]:
        return True
    if len(re.sub(r"[^A-Z]", "", word)) > 1:
        return True
    if word[-1] == "." and (not is_abbreviation(word)):
        return True
    return False


def split_into_sentences(text):
    potential_end_pat = re.compile(r"".join([
        r"([\w\.'’&\]\)]+[\.\?!])",  # A word that ends with punctuation
        r"([‘’“”'\"\)\]]*)",  # Followed by optional quote/parens/etc
        r"(\s+(?![a-z\-–—]))",  # Followed by whitespace + non-(lowercase or dash)
        ]), re.U)
    dot_iter = re.finditer(potential_end_pat, text)

    end_indices = []
    for x in dot_iter:
        if is_sentence_ender(x.group(1)):
            end_indices.append(x.start() + len(x.group(1)))

    spans = zip([None] + end_indices, end_indices + [None])
    sentences = [text[start:end].strip() for start, end in spans]
    return sentences
