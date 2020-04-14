import re
import os.path
import pandas as pd
from typing import Dict


class NLG:
    def __init__(self):
        self.html_tag = re.compile(r'<[^>]+>')
        self.newline = re.compile(r'\\n|\\t|\\b|\\r')
        self.dup_space = re.compile(r'\s+')
        self.templates = {}
        templates_df = pd.read_csv(os.path.join(os.path.dirname(__file__), 'templates.csv'), header=None, sep='|')
        for _, row in templates_df.iterrows():
            self.templates[row[0]] = row[1]

    def __call__(self, action, substitutes: Dict) -> str:
        response = self.templates[action].format(**substitutes)
        return self._clean(response)

    def _clean(self, text):
        text = self.html_tag.sub(' ', text)
        text = self.newline.sub(' ', text)
        text = self.dup_space.sub(' ', text)
        return text.strip()


