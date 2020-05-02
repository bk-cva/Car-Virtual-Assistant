import re
import csv
import os.path
from typing import Dict


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
        if action in self.templates:
            response = self.templates[action].format(**substitutes)
            return self._clean(response)
        return self.templates['default']

    def _clean(self, text):
        text = self.html_tag.sub(' ', text)
        text = self.newline.sub(' ', text)
        text = self.dup_space.sub(' ', text)
        return text.strip()


