"""Extracting and cleaning text from HTML posts"""

from bs4 import BeautifulSoup
import demoji
import spacy
from spacy_loader import get_spacy_model
from settings import STRINGS_TO_REMOVE

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

def filter_post_html(
        post_html: str,
        strings_to_remove: list[str]=STRINGS_TO_REMOVE
) -> str:
    """
    Cleans the HTML of the given post from the ML Algorithms Unpacked newsletter. Namely:
    - Converting all text to lowercase
    - Removal of emojis
    - Removal of common sections such as the conclusion
    - Removal of common phrases like "subscribe now"

    Parameters
    ----------
    post_html: str
        The HTMl of the post.
    strings_to_remove: list[str], optional
        The common phrases to remove from the post. Default is STRINGS_TO_REMOVE.

    Returns
    ----------
    paragraph_text: str
        The filtered text from the <p></p> tags of the HTML.
    """
    # post_contents = post.get_content()
    soup = BeautifulSoup(post_html, "html.parser")

    paragraphs = soup.find_all("p")  # Does not include things like headers
    paragraph_text = [text.text.lower() for text in paragraphs]
    paragraph_text = " ".join(paragraph_text)

    # Emoji removal
    paragraph_text = demoji.replace(paragraph_text)

    # Remove conclusion
    paragraph_text = paragraph_text.split("i hope you enjoyed reading")[0]

    for string in strings_to_remove:
        paragraph_text = paragraph_text.replace(string, "")

    return paragraph_text

def clean_text(text: str) -> list[str]:
    """
    Removes stop words, punctuation and blank spaces from the given text.

    Returns list of words in lemmatised form.
    """
    nlp = spacy.load("en_core_web_sm")
    # nlp = get_spacy_model()
    doc = nlp(text)  # Attaches useful metadata to clean_text

    # Remove stop words, punctuation and blank spaces
    filtered_tokens = [
        token for token in doc if not (
                token.is_stop or token.is_punct or token.is_space
        )
    ]

    # Lemmatisation
    filtered_tokens = [token.lemma_ for token in filtered_tokens]

    return filtered_tokens

def vectorise_text(posts_text_cleaned: list[str]) -> np.ndarray:
    """
    Applies TF-IDF to the text data of the input posts.

    Parameters
    ----------
    posts_text_cleaned: list[str]
        List of filtered, clean text.

    Returns
    ----------
    result: np.ndarray
        The matrix of TF-IDF values.

    """
    tfidf = TfidfVectorizer()
    result = tfidf.fit_transform(posts_text_cleaned)
    result = result.toarray()

    return result