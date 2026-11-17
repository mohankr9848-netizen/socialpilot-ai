"""Extensible interface; no paid API or local model required."""
from modules.business_analyzer import analyze

class TemplateProvider:
    name = 'Free evidence-based templates'
    def generate(self, business, crawl):
        return analyze(business, crawl)


def get_provider():
    return TemplateProvider()
