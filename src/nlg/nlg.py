import re
import csv
import logging
import os.path
from typing import Dict


logger = logging.getLogger(__name__)


class NLG:
    def __init__(self):
        self.html_tag = re.compile(r'<[^>]+>')
        self.newline = re.compile(r'\\n|\\t|\\b|\\r')
        self.dup_space = re.compile(r'\s+')
        self.templates = {}
        with open(os.path.join(os.path.dirname(__file__), 'templates.csv')) as csvfile:
            reader = csv.reader(csvfile, delimiter='|')
            for row in reader:
                self.templates[row[0]] = row[1]

    def __call__(self, action, substitutes: Dict) -> str:
        # preprocess substitutes
        for k, v in substitutes.items():
            if v is None:
                substitutes[k] = ''
        if 'street' in substitutes:
            substitutes['street'] = re.sub(r'^đường', '', substitutes['street'], flags=re.IGNORECASE)

        if action in self.templates:
            response = self.templates[action].format(**substitutes)
            return action, self._clean(response)
        logger.warning('No template found for \'{}\', use default.'.format(action))
        return action, self.templates['default']

    def _clean(self, text):
        text = self.html_tag.sub(' ', text)
        text = self.newline.sub(' ', text)
        text = self.dup_space.sub(' ', text)
        return text.strip()


