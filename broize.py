# -*- coding: utf-8 -*-

import random
from textblob import TextBlob, Word
from config import FILTER_WORDS

import logging

logging.basicConfig(level=logging.DEBUG)

# Sentences we'll respond with if we have no idea what the user is going to say
NOOP_RESPONSES = [
    u"Yeah it's not that simple",
    u"sorry not sorry",
    u"i have mad react skills",
    u"code hard bro",
    u"Want to bro down and crush code?",
]

# If the user tries to tell us something about ourselves
COMMENTS_ABOUT_SELF = [
    u"You're just jealous",
    u"I worked really hard on that",
    u"My Klout score is {}".format(random.randint(100, 500)),
]

SELF_VERBS_WITH_DOBJECT_CAPS_PLURAL = [
    u'My last startup totally crushed the {dobject} vertical',
    u'Were you aware I was a serial entrepreneur in the {dobject} sector?',
    u"My startup is Uber for {dobject}",
    u'I really consider myself an expert on {dobject}',
]

SELF_VERBS_WITH_DOBJECT_LOWER = [
    u'Yeah but I know a lot about {dobject}',
    u'My bros always ask me about {dobject}',
]

SELF_VERBS_WITH_ADJECTIVE = [
    u"I'm personally building the {adjective} Economy",
    u"I consider myself to be a {adjective}preneur",
]

# Raise this (uncaught) exception if the response was going to trigger our blacklist
class UnacceptableUtteranceException(Exception):
    pass


def starts_with_vowel(word):
    return True if word[0] in 'aeiou' else False

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
    if subject:
        logging.debug(u"Found subject: %s", subject)
    return subject

def find_object(sent):
    """Given a sentence, find the best candidate object."""
    dobject = None

    # Prefer noun phrases if possible
    for np in sent.noun_phrases:
        dobject = np
    if not dobject:
        for w, p in sent.pos_tags:
            print w, p
            if p == 'NN':  # This is a noun
                dobject = w
                break
    if dobject:
        logging.debug(u"Found dobject: %s", dobject)

    return dobject

def find_adjective(sent):
    """Given a sentence, find the best candidate adjective."""
    adj = None
    for w, p in sent.pos_tags:
        print w, p
        if p == 'JJ':  # This is an adjective
            adj = w
            break
    return adj

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
    if verb:
        logging.debug(u"Found verb: %s", verb)
    return verb, pos

def construct_response(subject, dobject, verb, verb_pos, adjective):
    """No special cases matched, so we're going to try to construct a full sentence that uses as much
    of the user's input as possible"""
    resp = []
    if subject:
        resp.append(subject)
    # We always respond in the present tense, and the subject will always either be a passthrough
    # from the user, or 'you' or 'I', in which case we might need to change the tense for some
    # irregular verbs.
    if verb:
        if verb.lemma == u'be':
            if subject.lower() == u'you':
                # The bot will always tell the person they aren't whatever they said they were
                resp.append(u"aren't really")
            else:
                resp.append(verb)
    if dobject:
        if starts_with_vowel(dobject):
            resp.append(u"an")
        else:
            resp.append(u"a")
        resp.append(dobject)

    resp.append(random.choice((u"tho", u"bro", u"lol", u"bruh", u"smh", u"")))

    if len(resp) > 0:
        return " ".join(resp)


def respond(sentence):
    resp = None
    subject = None
    dobject = None
    adjective = None
    verb = None

    parsed = TextBlob(sentence)

    # Loop through all the sentences, if more than one. This will help extract the most relevant
    # response text even across multiple sentences (for example if there was no obvious direct object
    # in one sentence

    for sent in parsed.sentences:
        subject = find_subject(sent)
        dobject = find_object(sent)
        adjective = find_adjective(sent)

    # If we said something about the bot and used some kind of direct object, construct the
    # sentence around that
    logging.debug("Subject=%s, dobject=%s, adjective=%s", subject, dobject, adjective)

    if subject == u'REFERS_TO_SELF' and (dobject or adjective):
        if dobject:
            if random.choice((True, False)):
                resp = random.choice(SELF_VERBS_WITH_DOBJECT_CAPS_PLURAL).format(**{'dobject': dobject.pluralize().capitalize()})
            else:
                resp = random.choice(SELF_VERBS_WITH_DOBJECT_LOWER).format(**{'dobject': dobject})
        else:
            resp = random.choice(SELF_VERBS_WITH_ADJECTIVE).format(**{'adjective': adjective})
    else:
        for sent in parsed.sentences:
            verb, verb_pos = find_verb(sent)

    if not resp:
        # If we didn't override the final sentence, try to construct a new one:
        if not subject:
            resp = random.choice(NOOP_RESPONSES)
        elif subject == u'REFERS_TO_SELF' and not verb:
            resp = random.choice(COMMENTS_ABOUT_SELF)
        else:
           resp = construct_response(subject, dobject, verb, verb_pos, adjective)

    # If we got through all that with nothing, use a random response
    if not resp:
        resp = random.choice(NOOP_RESPONSES)

    logging.debug(u"Returning phrase '%s'", resp)
    # Check that we're not going to say anything obviously offensive
    filter_response(resp)

    return resp

def filter_response(resp):
    """Don't allow any words to match our filter list"""
    parsed = TextBlob(resp)
    for word in parsed.words:
        if '@' in word or '#' in word or '!' in word:
            raise UnacceptableUtteranceException()
        for s in FILTER_WORDS:
            if word.lower().startswith(s):
                raise UnacceptableUtteranceException()
