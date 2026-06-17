"""Streamlit webapp"""

import json
from collections import Counter
import numpy as np
import pandas as pd

from substack_api import Newsletter, Category
from database import access_supabase_data
from settings import STRINGS_TO_REMOVE
from clustering import cluster_text_and_report

# Project files
from substack_client import newsletters_to_df, posts_to_df
from text_processing import filter_post_html, clean_text, vectorise_text

# Plotting
import plotly.express as px

# Display
import streamlit as st

st.set_page_config(page_title="Substack Analysis", layout="wide")

@st.cache_data(show_spinner="Loading publication data...")
def load_newsletter_from_database() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Loads data on top posts and all posts from the given newsletter.

    Parameters
    ----------
    newsletter_url: str
        The URL of the newsletter to load data from.

    Returns
    ----------
    top_posts, all_posts: tuple[pd.DataFrame, pd.DataFrame]
        DataFrames with the top posts (according to Substack's ranking criteria) and all posts respectively.
    """
    all_posts_str = access_supabase_data('All posts').model_dump_json()
    all_posts_json = json.loads(all_posts_str)
    all_posts = pd.DataFrame(all_posts_json['data'])

    top_posts = all_posts.sort_values(by=['Likes'], ascending=False)[:5]

    return top_posts, all_posts

@st.cache_data(show_spinner="Creating word embeddings...")
def create_word_embeddings() -> np.ndarray:
    cleaned_text = access_supabase_data('MLAU cleaned text').model_dump_json()
    cleaned_text_json = json.loads(cleaned_text)
    cleaned_text_df = pd.DataFrame(cleaned_text_json['data'])

    embeddings = vectorise_text(cleaned_text_df['Cleaned text'])

    return embeddings

@st.cache_data(show_spinner="Loading category...")
def load_queried_category_metadata(
    category_name: str,
    query: str
):
    """
    Loads newsletters in category according to the given query.

    Parameters
    ----------
    category_name: str
        The name of the Substack category to load data from.
    query: str
        The (non-Regex) query to search category newsletters for.

    Returns
    ----------
    """
    # TODO
    # Export query-related data to Supabase (complete export_filtered_category_data())
    # Read in Supabase contents here

@st.cache_data(show_spinner="Loading category data...")
def load_category_metadata(
        category_name: str,
        return_num: int=None
) -> list[dict]:
    """
    Load metadata for all newsletters in the given category.

    Parameters
    ----------
    category_name: str
        The name of the Substack category to load data from.
    return_num: int, optional
        The number of newsletters to return. Default is 0, for which all newsletters are returned.

    Returns
    -------
    newsletters_metadata: list[dict]
        A list whose elements each correspond to a newsletter from the category.
    """
    category = Category(name=category_name)
    newsletters_metadata = category.get_newsletter_metadata()

    if return_num:
        return newsletters_metadata[:return_num]
    else:
        return newsletters_metadata

def word_frequency_plot(
        word_list: list[str],
        top_n: int = 10
):
    """
    Creates a bar plot of word counts, ordered by frequency.
    """
    word_freq = Counter(word_list)

    words, counts = zip(*word_freq.most_common(top_n))

    fig = px.bar(
        x = words,
        y=counts,
        labels={"x": "Words", "y": "Frequency"},
        title=f"Top {top_n} word frequencies (lemmatised)"
    )

    return fig

def post_eda(post_html: str):
    """
    Extracts the text from the HTML form of a Substack post and displays relevant plots.
    """
    top_post_text = filter_post_html(
        post_html=post_html,
        strings_to_remove=STRINGS_TO_REMOVE
    )

    top_post_text_clean = clean_text(top_post_text)

    fig = word_frequency_plot(top_post_text_clean)
    st.plotly_chart(fig)

def run_dashboard() -> None:
    st.title("📦 Machine Learning Algorithms Unpacked 📦")

    personal_tab, others_tab = st.tabs(['Personal', 'Other'])

    with personal_tab:
        top_posts, all_posts = load_newsletter_from_database()

        with st.container():
            st.header("Top 5 posts")

            top_posts = top_posts.drop(columns=['created_at'])
            st.dataframe(
                top_posts,
                hide_index=True,
                column_config={
                    "URL": st.column_config.LinkColumn(
                        label="Article URL",
                    )
                }
            )

        with st.container():
            # Clustering
            st.subheader("DBSCAN results")

            # plot1, sliders, plot2 = st.columns(3)

            embeddings = create_word_embeddings()
            dbscan = cluster_text_and_report(
                posts=all_posts[['Title', 'URL']],
                word_embeddings=embeddings,
                model_params={'eps': 1, 'min_samples': 2},
                n_components=2,
                plot_title='DBSCAN results (with PCA)',
            )
            st.plotly_chart(
                dbscan.fig,
                width='content'
            )

            with st.form("new_dbscan"):
                # Other options for DBSCAN
                eps_slider = st.slider(
                    "Eps parameter",
                    min_value=0.0,
                    max_value=10.0,
                    value=1.0,
                    step=0.25
                )
                min_samples_slider = st.slider(
                    "Min samples parameter",
                    min_value=1,
                    max_value=20,
                    value=2,
                    step=1
                )
                dbscan_button = st.form_submit_button(label="Run new DBSCAN")
                # dbscan_button = st.checkbox('Run new DBSCAN')

                if dbscan_button:
                    dbscan_new = cluster_text_and_report(
                        posts=all_posts[['Title', 'URL']],
                        word_embeddings=embeddings,
                        model_params={'eps': eps_slider, 'min_samples': min_samples_slider},
                        n_components=2,
                        plot_title='New DBSCAN results (with PCA)'
                    )
                    st.plotly_chart(
                        dbscan_new.fig,
                        width='content'
                    )


        with st.container():
            # Analytics
            st.subheader("Top post analytics")

            top_post_title_option = st.selectbox(
                "Select top post to analyse",
                top_posts['Title'],
            )

            top_post = top_posts.loc[top_posts['Title'] == top_post_title_option, 'Post HTML'].iloc[0]
            post_eda(top_post)

        with st.container():
            st.header("Publication stats")

            # Extra features
            all_posts['Date of upload'] = pd.to_datetime(all_posts['Date of upload'])
            all_posts['Hour of upload'] = all_posts['Date of upload'].dt.hour

            # Word counts
            fig_word_count = px.bar(all_posts, x='Date of upload', y='Word count', title="Word counts over time")
            st.plotly_chart(fig_word_count, key="word_count")

            # Hour of upload consistency
            fig_hour = px.bar(all_posts, x='Date of upload', y='Hour of upload', title="Hour of upload")
            st.plotly_chart(fig_hour, key="hour_of_upload")

            st.subheader("Tabular stats")

            all_posts = all_posts.drop(columns=['created_at'])
            st.dataframe(
                all_posts,
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