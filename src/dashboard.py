import pandas as pd
from substack_api import Newsletter, Post
import streamlit as st

st.set_page_config(page_title="Substack Analysis", layout="wide")

@st.cache_data
def load_data(newsletter_url: str) -> tuple[list, list]:
    newsletter = Newsletter(newsletter_url)
    top_posts = newsletter.get_posts(sorting="top", limit=5)
    recent_posts = newsletter.get_posts(limit=5)

    return top_posts, recent_posts

def posts_to_df(posts: list[Post]) -> pd.DataFrame:
    top_titles_metadata = [post.get_metadata() for post in posts]
    top_titles = [
        {
            'Title': metadata['title'],
            'URL': metadata['canonical_url'],
            'Word count': metadata['wordcount'],
            'Likes': metadata['reaction_count']
        }
        for metadata in top_titles_metadata
    ]

    return pd.DataFrame(top_titles)

def run_dashboard() -> None:
    st.title("Machine Learning Algorithms Unpacked: Analysis")

    top_posts, recent_posts = load_data(newsletter_url="https://ameersaleem.substack.com")

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

    with st.container():
        st.header("Recent posts")

        recent_posts = posts_to_df(recent_posts)

        st.dataframe(
            recent_posts,
            hide_index=True,
            column_config={
                "URL": st.column_config.LinkColumn(
                    label="Article URL",
                )
            }
        )

def main():
    run_dashboard()

if __name__ == '__main__':
    main()