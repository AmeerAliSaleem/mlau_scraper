from collections import Counter

# Text cleaning
from bs4 import BeautifulSoup
import demoji
import spacy

# Data handling
import pandas as pd
from substack_api import Newsletter, Post, Category

# Plotting
import plotly.express as px

# Display
from typing import Tuple, List
import streamlit as st

st.set_page_config(page_title="Substack Analysis", layout="wide")

@st.cache_data
def load_newsletter_data(newsletter_url: str) -> Tuple[List[Post], List[Post]]:
    """
    Loads data on top posts and recent posts from the given newsletter.
    """
    newsletter = Newsletter(newsletter_url)
    top_posts = newsletter.get_posts(sorting="top", limit=5)
    recent_posts = newsletter.get_posts(sorting="new")

    return top_posts, recent_posts

@st.cache_data
def load_category_metadata(category_name: str, return_num: int = 0) -> List[dict]:
    category = Category(name=category_name)
    # newsletters = category.get_newsletters()
    newsletters_metadata = category.get_newsletter_metadata()

    if return_num > 0:
        return newsletters_metadata[:return_num]
    else:
        return newsletters_metadata

def newsletters_to_df(newsletters_metadata: List[dict]) -> pd.DataFrame:
    """
    Extracts useful statistics from the given list of newsletters.
    """
    sorted_newsletters = sorted(
        newsletters_metadata,
        key=lambda x: int(x['freeSubscriberCount'].replace(',', '')) if x['freeSubscriberCount'] is not None else 0,
        reverse=True
    )

    top_newsletters = [
        {
            'Name': metadata['name'],
            'URL': metadata['base_url'],
            'Subscriber count': metadata['freeSubscriberCount'],
        }
        for metadata in sorted_newsletters
    ]

    return pd.DataFrame(top_newsletters)

def posts_to_df(posts: List[Post]) -> pd.DataFrame:
    """
    Extracts useful statistics from the list of posts of the given newsletter.
    """
    top_titles_metadata = [post.get_metadata() for post in posts]
    top_titles = [
        {
            'Title': metadata['title'],
            'URL': metadata['canonical_url'],
            'Date of upload': pd.to_datetime(metadata['post_date']),
            'Word count': metadata['wordcount'],
            'Likes': metadata['reaction_count'],
            'Restacks': metadata['restacks'],
            "No. of comments (exc. replies)": metadata['comment_count'] - metadata['child_comment_count']
        }
        for metadata in top_titles_metadata
    ]

    return pd.DataFrame(top_titles)

def filter_post_html(post: Post, strings_to_remove: List[str]) -> str:
    """
    Cleans the HTML of the given post from the ML Algorithms Unpacked newsletter. Namely:
    * Converting all text to lowercase
    * Removal of emojis
    * Removal of common sections such as the conclusion
    * Removal of common phrases like "subscribe now"
    """
    post_contents = post.get_content()
    soup = BeautifulSoup(post_contents, "html.parser")

    paragraphs = soup.find_all("p")  # Does not include things like headers
    paragraph_text = [text.text.lower() for text in paragraphs]
    paragraph_text = " ".join(paragraph_text)

    # Emoji removal
    paragraph_text = demoji.replace(paragraph_text)

    # Remove conclusion
    paragraph_text = paragraph_text.split("i hope you enjoyed reading")[0]

    # Remove arbitrarily common words/phrases
    strings_to_remove = [
        "hello fellow machine learners,",
        "subscribe now",
        "last week,",
        "this week"
    ]

    for string in strings_to_remove:
        paragraph_text = paragraph_text.replace(string, "")

    return paragraph_text

def clean_text(text: str) -> List[str]:
    """
    Removes stop words, punctuation and blank spaces from the given text.

    Returns list of words in lemmatised form.
    """
    nlp = spacy.load("en_core_web_sm")
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

def word_frequency_plot(word_list: List[str], top_n: int = 10):
    word_freq = Counter(word_list)

    words, counts = zip(*word_freq.most_common(top_n))

    fig = px.bar(
        x = words,
        y=counts,
        labels={"x": "Words", "y": "Frequency"},
        title=f"Top {top_n} word frequencies"
    )

    return fig

def run_dashboard() -> None:
    st.title("📦 Machine Learning Algorithms Unpacked 📦")

    personal_tab, others_tab = st.tabs(['Personal', 'Other'])

    with personal_tab:
        top_posts, recent_posts = load_newsletter_data(
            newsletter_url="https://ameersaleem.substack.com"
        )

        with st.container():
            st.header("Top posts")

            top_posts_df = posts_to_df(top_posts)

            st.dataframe(
                top_posts_df,
                hide_index=True,
                column_config={
                    "URL": st.column_config.LinkColumn(
                        label="Article URL",
                    )
                }
            )

            # Analytics
            st.subheader("Analytics for top post")

            top_post_text = filter_post_html(
                post=top_posts[0],
                strings_to_remove=[
                    "hello fellow machine learners,",
                    "subscribe now",
                    "last week,",
                    "this week"
                ]
            )

            top_post_text_clean = clean_text(top_post_text)

            fig = word_frequency_plot(top_post_text_clean)
            st.plotly_chart(fig)

        with st.container():
            st.header("Publication stats")

            recent_posts_df = posts_to_df(recent_posts)

            # Extra features
            recent_posts_df['Hour of upload'] = recent_posts_df['Date of upload'].dt.hour

            # Time series
            fig_word_count = px.line(recent_posts_df, x='Date of upload', y='Word count', title="Word counts over time")
            st.plotly_chart(fig_word_count, key="word_count")

            # Hour of upload consistency
            fig_hour = px.bar(recent_posts_df, x='Date of upload', y='Hour of upload', title="Hour of upload")
            st.plotly_chart(fig_hour, key="hour_of_upload")

            st.subheader("Tabular stats")
            st.dataframe(
                recent_posts_df,
                hide_index=True,
                column_config={
                    "URL": st.column_config.LinkColumn(
                        label="Article URL",
                    )
                }
            )

    with others_tab:
        top_tech_newsletters = load_category_metadata(
            category_name="Technology",
            # return_num=5
        )

        with st.container():
            st.header("Top tech newsletters")

            top_tech_newsletters_df = newsletters_to_df(top_tech_newsletters)

            st.dataframe(
                top_tech_newsletters_df,
                hide_index=True,
                column_config={
                    "URL": st.column_config.LinkColumn(
                        label="Newsletter URL",
                    )
                }
            )

def main():
    run_dashboard()

if __name__ == '__main__':
    main()