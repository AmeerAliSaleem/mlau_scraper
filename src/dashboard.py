from collections import Counter

from substack_api import Newsletter, Post, Category

# Project files
from substack_client import newsletters_to_df, posts_to_df
from text_processing import filter_post_html, clean_text

# Plotting
import plotly.express as px

# Display
import streamlit as st

st.set_page_config(page_title="Substack Analysis", layout="wide")

@st.cache_data
def load_newsletter_data(newsletter_url: str) -> tuple[list[Post], list[Post]]:
    """
    Loads data on top posts and recent posts from the given newsletter.
    """
    newsletter = Newsletter(newsletter_url)
    top_posts = newsletter.get_posts(sorting="top", limit=5)
    recent_posts = newsletter.get_posts(sorting="new")

    return top_posts, recent_posts

@st.cache_data
def load_category_metadata(category_name: str, return_num: int = 0) -> list[dict]:
    category = Category(name=category_name)
    # newsletters = category.get_newsletters()
    newsletters_metadata = category.get_newsletter_metadata()

    if return_num > 0:
        return newsletters_metadata[:return_num]
    else:
        return newsletters_metadata

def word_frequency_plot(word_list: list[str], top_n: int = 10):
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
            fig_word_count = px.bar(recent_posts_df, x='Date of upload', y='Word count', title="Word counts over time")
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