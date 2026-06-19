"""Constants and metadata for Substack scraping and analysis."""

NEWSLETTER_URL = 'https://ameersaleem.substack.com'

STRINGS_TO_REMOVE = [
    "hello fellow machine learners,",
    "subscribe now",
    "last week,",
    "this week"
]

MODEL = "en_core_web_sm"