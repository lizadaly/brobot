from __future__ import print_function, unicode_literals
import random
import logging
import os

os.environ['NLTK_DATA'] = os.getcwd() + '/nltk_data'

from textblob import TextBlob
from config import FILTER_WORDS

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# start:example-hello.py
# Sentences we'll respond with if the user greeted us
GREETING_KEYWORDS = (
    "hello",
    "hi",
    "greetings",
    "sup",
    "what's up",
)
GREETING_RESPONSES = [
    "'sup bro",
    "hey",
    "*nods*",
    "hey you get my snap?"
]
def check_for_greeting(sentence):
    """If any of the words in the user's input was a greeting,
    return a greeting response"""
    for word in sentence.words:
        if word in GREETING_KEYWORDS:
            return random.choice(GREETING_RESPONSES)
# end

# start:example-none.py
# Sentences we'll respond with if we have no idea what the user just said
NONE_RESPONSES = [
    "uh whatever",
    "meet me at the foosball table, bro?",
    "code hard bro",
    "want to bro down and crush code?",
]
# end

# start:example-self.py
# If the user tries to tell us something about ourselves, use one of these responses
COMMENTS_ABOUT_SELF = [
    "You're just jealous",
    "I worked really hard on that",
    "My Klout score is {}".format(random.randint(100, 500)),
]
# end

# start:example-dobject.py
# Template for responses that include a direct object which is indefinite/uncountable
SELF_VERBS_WITH_DOBJECT_CAPS_PLURAL = [
    "My last startup totally crushed the {dobject} vertical",
    "Were you aware I was a serial entrepreneur in the {dobject} sector?",
    "My startup is Uber for {dobject}",
    "I really consider myself an expert on {dobject}",
]
# end

SELF_VERBS_WITH_DOBJECT_LOWER = [
    "Yeah but I know a lot about {dobject}",
    "My bros always ask me about {dobject}",
]

# start:example-adjective.py
SELF_VERBS_WITH_ADJECTIVE = [
    "I'm personally building the {adjective} Economy",
    "I consider myself to be a {adjective}preneur",
]
# end

class UnacceptableUtteranceException(Exception):
    """Raise this (uncaught) exception if the response was going to trigger our blacklist"""
    pass


def starts_with_vowel(word):
    """Check for pronoun compability -- 'a' vs. 'an'"""
    return True if word[0] in 'aeiou' else False


def broback(sentence):
    """Main program loop: select a response for the input sentence and return it"""
    logger.info("Broback: respond to %s", sentence)
    resp = respond(sentence)
    return resp


# start:example-subject.py
def find_subject(sent):
    """Given a sentence, find a preferred subject to respond with. Returns None if no candidate
    subject is found in the input"""
    subject = None

    for w, p in sent.pos_tags:
        # Disambiguate pronouns
        if p == 'PRP' and w.lower() == 'you':
            subject = 'I'
        elif p == 'PRP' and w == 'I':
            # If the user mentioned themselves, then they will definitely be the subject
            subject = 'You'

    if subject:
        logger.info("Found subject: %s", subject)
    return subject
# end


def find_object(sent):
    """Given a sentence, find the best candidate object."""
    dobject = None

    if not dobject:
        for w, p in sent.pos_tags:
            if p == 'NN':  # This is a noun
                dobject = w
                break
    if dobject:
        logger.info("Found dobject: %s", dobject)

    return dobject

def find_adjective(sent):
    """Given a sentence, find the best candidate adjective."""
    adj = None
    for w, p in sent.pos_tags:
        if p == 'JJ':  # This is an adjective
            adj = w
            break
    return adj

# start:example-verb.py
# Reference for verb part-of-speech tags:
# https://www.ling.upenn.edu/courses/Fall_2003/ling001/penn_treebank_pos.html
def find_verb(sent):
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
        logger.info("Found verb: %s", verb)
    return verb, pos
# end

# start:example-construct-response.py
def construct_response(subject, dobject, verb):
    """No special cases matched, so we're going to try to construct a full sentence that uses as much
    of the user's input as possible"""
    resp = []
    if subject:
        resp.append(subject)
    # We always respond in the present tense, and the subject will always either be a passthrough
    # from the user, or 'you' or 'I', in which case we might need to change the tense for some
    # irregular verbs.
    if verb:
        verb_word = verb[0]
        if verb_word in ('be', 'am', 'is', "'m"):  # This would be an excellent place to use lemmas!
            if subject.lower() == 'you':
                # The bot will always tell the person they aren't whatever they said they were
                resp.append("aren't really")
            else:
                resp.append(verb_word)
    if dobject:
        if starts_with_vowel(dobject):
            resp.append("an")
        else:
            resp.append("a")
        resp.append(dobject)

    resp.append(random.choice(("tho", "bro", "lol", "bruh", "smh", "")))

    if len(resp) > 0:
        return " ".join(resp)
# end

# start:example-find-candidate.py
def find_candidate_parts_of_speech(parsed):
    """Given a parsed input, find the best subject, direct object, adjective, and verb to match their input.
    Returns a tuple of subject, dobject, adjective, verb any of which may be None if there was no good match"""
    subject = None
    dobject = None
    adjective = None
    verb = None
    for sent in parsed.sentences:
        subject = find_subject(sent)
        dobject = find_object(sent)
        adjective = find_adjective(sent)
        verb = find_verb(sent)
    logger.info("Subject=%s, dobject=%s, adjective=%s, verb=%s", subject, dobject, adjective, verb)
    return subject, dobject, adjective, verb
# end

# start:example-check-for-self.py
def check_for_comment_about_bot(subject, dobject, adjective):
    """Check if the user's input was about the bot itself, in which case try to fashion a response
    that feels right based on their input. Returns the new best sentence, or None."""

    resp = None
    if subject == 'I' and (dobject or adjective):
        if dobject:
            if random.choice((True, False)):
                resp = random.choice(SELF_VERBS_WITH_DOBJECT_CAPS_PLURAL).format(**{'dobject': dobject.pluralize().capitalize()})
            else:
                resp = random.choice(SELF_VERBS_WITH_DOBJECT_LOWER).format(**{'dobject': dobject})
        else:
            resp = random.choice(SELF_VERBS_WITH_ADJECTIVE).format(**{'adjective': adjective})
    return resp
# end

def preprocess_text(sentence):
    """Handle some weird edge cases in parsing, like 'i' needing to be capitalized
    to be correctly identified as a pronoun"""
    cleaned = []
    words = sentence.split(' ')
    for w in words:
        if w == 'i':
            w = 'I'
        if w == "i'm":
            w = "I'm"
        cleaned.append(w)

    return ' '.join(cleaned)

# start:example-respond.py
def respond(sentence):
    """Parse the user's inbound sentence and find candidate terms that make up a best-fit response"""
    cleaned = preprocess_text(sentence)
    parsed = TextBlob(cleaned)

    # Loop through all the sentences, if more than one. This will help extract the most relevant
    # response text even across multiple sentences (for example if there was no obvious direct object
    # in one sentence
    subject, dobject, adjective, verb = find_candidate_parts_of_speech(parsed)

    # If we said something about the bot and used some kind of direct object, construct the
    # sentence around that, discarding the other candidates
    resp = check_for_comment_about_bot(subject, dobject, adjective)

    # If we just greeted the bot, we'll use a return greeting
    if not resp:
        resp = check_for_greeting(parsed)

    if not resp:
        # If we didn't override the final sentence, try to construct a new one:
        if not subject:
            resp = random.choice(NONE_RESPONSES)
        elif subject == 'I' and not verb:
            resp = random.choice(COMMENTS_ABOUT_SELF)
        else:
            resp = construct_response(subject, dobject, verb)

    # If we got through all that with nothing, use a random response
    if not resp:
        resp = random.choice(NONE_RESPONSES)

    logger.info("Returning phrase '%s'", resp)
    # Check that we're not going to say anything obviously offensive
    filter_response(resp)

    return resp
# end

# start:example-filter.py
def filter_response(resp):
    """Don't allow any words to match our filter list"""
    parsed = TextBlob(resp)
    for word in parsed.words:
        if '@' in word or '#' in word or '!' in word:
            raise UnacceptableUtteranceException()
        for s in FILTER_WORDS:
            if word.lower().startswith(s):
                raise UnacceptableUtteranceException()
# end
