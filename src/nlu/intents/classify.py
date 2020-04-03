import spacy
import pickle
import os.path

from ..common import MODEL_DIR
from .regexer import classify_by_regex
from .constants import Intent

CLASSIFIER_PATH = os.path.join(MODEL_DIR, 'clf.sav')

nlp = spacy.load('vi_spacy_model')
clf = pickle.load(open(CLASSIFIER_PATH, mode='rb'))


def predict_intent(text: str) -> Intent:
    """Predict intent of a string"""
    regex_intent = classify_by_regex(text)
    if regex_intent:
        return Intent(regex_intent)
    x = nlp(text).vector
    return Intent(clf.predict([x])[0])
