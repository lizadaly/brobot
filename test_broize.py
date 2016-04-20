import pytest

from broize import *

def test_random_utterance():
    """An utterance which is unparsable should return one of the random responses"""
    random.seed(0)
    sent = "abcd"  # Something unparseable
    resp = broback(sent)
    assert resp == NOOP_RESPONSES[0]

def test_contains_reference_to_user():
    """An utterance where the user mentions themselves should specifically return a phrase starting with 'You'"""
    sent = "I'm good at Python programming"
    resp = broback(sent)
    assert resp.startswith('You')

def test_contains_reference_to_bot():
    """An utterance where the user directs something at the bot itself should return a canned response"""
    random.seed(0)
    sent = "You are lame"
    resp = broback(sent)
    assert resp == 'I consider myself to be a lamepreneur'

def test_reuses_subject():
    """If the user tells us about some kind of subject, we should mention it in our response"""
    sent = "I am a capable programmer"
    resp = broback(sent)
    assert "programmer" in resp

def test_strip_offensive_words():
    """Don't allow the bot to respond with anything obviously offensive"""
    # To avoid including an offensive word in the test set, add a harmless word temporarily
    from config import FILTER_WORDS
    FILTER_WORDS.add('snakeperson')
    sent = "I am a snakeperson"
    with pytest.raises(UnacceptableUtteranceException):
        broback(sent)

def test_strip_punctuation():
    """Removing most punctuation is one way to ensure that the bot doesn't include hashtags or @-signs, which are potential vectors for harrassment"""
    pass
