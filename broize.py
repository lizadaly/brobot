import random
from textblob import TextBlob
from config import FILTER_WORDS

import logging

logging.basicConfig(level=logging.DEBUG)

# Sentences we'll respond with if we have no idea what the user is going to say
NOOP_RESPONSES = (
    "Yeah it's not that simple",
)

# If the user tries to tell us something about ourselves
COMMENTS_ABOUT_SELF = (
    "You're just jealous",
    "I worked really hard on that",
)

SELF_VERBS_WITH_DOBJECT = (
    'I know a lot about {dobject}',
    'I really consider myself an expert on {dobject}',
    'My last startup totally crushed the {dobject} vertical',
    'Were you aware I was a serial entrepreneur in the {dobject} sector'
    'Let me tell about how I intend to disrupt {dobject}',
    "It's like Uber for {dobject}",
)

# Raise this (uncaught) exception if the response was going to trigger our blacklist
class UnacceptableUtteranceException(Exception):
    pass


def broback(sentence):

    resp = respond(sentence)

    return resp

def find_subject(sent):
    """Given a sentence, find a preferred subject to respond with. Returns None if no candidate
    subject is found in the input"""
    subject = None

    for w, p in sent.pos_tags:
        # Disambiguate pronouns
        if p == 'PRP' and w == 'I':
            # If the user mentioned themselves, then they will definitely be the subject
            subject = 'You'
        elif p == 'PRP' and w == 'You':
            subject = 'REFERS_TO_SELF'
    return subject

def find_object(sent):
    """Given a sentence, find the best candidate object."""
    dobject = None

    # Prefer noun phrases if possible
    for np in sent.noun_phrases:
        dobject = np
    if not dobject:
        for w, p in sent.pos_tags:
            if p == 'NN':  # This is a noun
                dobject = w
                break
    return dobject

# Reference for verb part-of-speech tags:
# https://www.ling.upenn.edu/courses/Fall_2003/ling001/penn_treebank_pos.html
def find_verb(sent, subject=None, dobject=None):
    """Pick a candidate verb for the sentence. Influenced by whether we already know that we've
    selected a subject or direct object"""
    verb = None
    pos = None
    for w, p in sent.pos_tags:
        if p.startswith('VB'):  # This is a verb
            verb = w
            pos = p
            break
    return verb, pos

def respond(sentence):
    resp = None
    subject = None
    dobject = None
    verb = None

    parsed = TextBlob(sentence)

    # Loop through all the sentences, if more than one. This will help extract the most relevant
    # response text even across multiple sentences (for example if there was no obvious direct object
    # in one sentence

    for sent in parsed.sentences:
        subject = find_subject(sent)
        dobject = find_object(sent)

    # If we said something about the bot and used some kind of direct object, construct the
    # sentence around that
    logging.debug("Subject={}, dobject={}".format(subject, dobject))

    if subject == 'REFERS_TO_SELF' and dobject:
        resp = random.choice(SELF_VERBS_WITH_DOBJECT).format(**{'subject': subject, 'dobject': dobject})
    else:
        for sent in parsed.sentences:
            verb, verb_pos = find_verb(sent)

    if not resp:
        logging.debug("Subject={}, dobject={}, verb={}".format(subject, dobject, verb))

    # If we didn't override the final sentence, try to construct a new one:

    if not resp:
        if not subject:
            resp = random.choice(NOOP_RESPONSES)
        elif subject == 'REFERS_TO_SELF' and not verb:
            resp = random.choice(COMMENTS_ABOUT_SELF)

    # If we got through all that with nothing, use a random response
    if not resp:
        resp = random.choice(NOOP_RESPONSES)

    logging.debug("Returning phrase '{}'".format(resp))
    # Check that we're not going to say anything obviously offensive
    filter_response(resp)

    return resp

def filter_response(resp):
    """Don't allow any words to match our filter list"""
    parsed = TextBlob(resp)
    for word in parsed.words:
        for s in FILTER_WORDS:
            if word.startswith(s):
                raise UnacceptableUtteranceException()
