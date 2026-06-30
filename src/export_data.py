"""Save Substack API results to database"""

import datetime
import pandas as pd
import logging

from substack_api import Category, Newsletter
from substack_client import (load_newsletter_data, newsletters_to_df,
                             filter_newsletters_in_category, posts_to_df)
from text_processing import filter_post_html, clean_text
from database import supabase_to_df, save_to_supabase
from settings import STRINGS_TO_REMOVE, NEWSLETTER_URL

# TODO
# - Run main and check that export_filtered_posts() works
# - Check that export_filtered_newsletters() works
# - Check that export_posts_cleaned_text() and remove commented lines if so


# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def json_serialisable(obj):
    """
    Convert data types that are incompatible with JSON.
    """
    if isinstance(obj, datetime.datetime):
        # Deal with pd.NaT first
        if pd.isna(obj):
            return ""
        return obj.strftime('%Y-%m-%d %H:%M:%S')

    return obj

def export_newsletter_data(newsletter_url: str=NEWSLETTER_URL) -> None:
    """
    A function to scrape Substack data and store the results in Supabase.
    """
    all_posts = load_newsletter_data(
        newsletter_url=newsletter_url
    )
    all_posts_df = posts_to_df(all_posts)

    for col in all_posts_df.columns:
        all_posts_df[col] = all_posts_df[col].apply(json_serialisable)

    save_to_supabase(
        df=all_posts_df.to_dict(orient='records'),
        table_name='All posts',
        upsert=True
    )

def export_posts_cleaned_text(
    raw_database_name: str,
    target_database_name: str,
) -> None:
    """
    Cleans text of newsletter's posts and stores the results in the corresponding Supabase table.

    Parameters
    ----------
    raw_database_name: str
        The name of the Supabase table where the raw Substack post data is stored.
    target_database_name: str
        The name of the Supabase table to save the results to.
    """
    # posts_str = access_supabase_data(table_name=raw_database_name).model_dump_json()
    # posts_json = json.loads(posts_str)
    # posts_df = pd.DataFrame(posts_json['data'])

    posts_df = supabase_to_df(table_name=raw_database_name)

    posts_html = posts_df['Post HTML']
    posts_text = [
        filter_post_html(
            post_html=post_html,
            strings_to_remove=STRINGS_TO_REMOVE
        ) for post_html in posts_html
    ]

    posts_text_cleaned = [
        ' '.join(clean_text(text)) for text in posts_text
    ]

    cleaned_text_df = pd.DataFrame(
        {
            'id': posts_df['id'],
            'Title': posts_df['Title'],
            'Cleaned text': posts_text_cleaned
        }
    )

    # Save to Supabase
    save_to_supabase(
        df=cleaned_text_df.to_dict(orient='records'),
        table_name=target_database_name,
        upsert=True
    )

def export_filtered_newsletters(
    category_name: str,
    query: str,
    newsletters_table_name: str,
    newsletter_limit: int=10
):
    """
    A function that:
    - Makes a call to the Substack API to retrieve the newsletters in the given category
    - Filters the newsletters based on the given query
    - Saves the results in the corresponding Supabase table

    Parameters
    ----------
    category_name: str
        The name of the Substack category to filter on.
    query: str
        The query to filter newsletters on.
    newsletters_table_name : str
        The name of the Supabase table to save the newsletters data to.
    newsletter_limit: int, optional
        The number of newsletters in the category to filter on. Default is 10.
    """
    category = Category(category_name)

    filtered_newsletters, newsletter_to_posts = filter_newsletters_in_category(
        category=category,
        query=query,
        newsletter_limit=newsletter_limit
    )

    # --- Exporting filtered_newsletters ---
    filtered_newsletters_df = newsletters_to_df(filtered_newsletters)

    # Make json safe
    for col in filtered_newsletters_df.columns:
        filtered_newsletters_df[col] = filtered_newsletters_df[col].apply(json_serialisable)

    filtered_newsletters_df = filtered_newsletters_df.fillna('')

    save_to_supabase(
        df=filtered_newsletters_df.to_dict(orient='records'),
        table_name=newsletters_table_name,
        upsert=True
    )

def export_filtered_posts(
        newsletters: list[Newsletter],
        query: str,
        posts_table_name: str,
        post_limit: int = None
) -> None:
    """
    Takes a list of filtered newsletters, searches for the posts related to the given query
    and saves their information to Supabase.

    Parameters
    ----------
    newsletters : list[Newsletter]
        The newsletters with posts filtered by `query`.
    query : str
        The query that the newsletters were filtered with respect to, e.g. "machine learning".
    posts_table_name : str
        The name of the Supabase table to save the posts data to.
    post_limit : int, optional
        The maximum number of `query`-relevant posts to return for each newsletter.
        Default is None, returning all the `query`-relevant posts.
    """
    posts_to_export = []
    for newsletter in newsletters:
        filtered_posts = newsletter.search_posts(query=query, limit=post_limit)
        newsletter_posts_df = posts_to_df(filtered_posts)

        # Drop duplicate articles (newsletter keyword searching does not remove dupes)
        newsletter_posts_df = newsletter_posts_df.drop_duplicates()

        # Make json safe
        for col in newsletter_posts_df.columns:
            newsletter_posts_df[col] = newsletter_posts_df[col].apply(json_serialisable)

        newsletter_posts_df = newsletter_posts_df.fillna('')
        posts_to_export.append(newsletter_posts_df)

    posts_to_export_full = pd.concat(posts_to_export, ignore_index=True)
    save_to_supabase(
        df=posts_to_export_full.to_dict(orient='records'),
        table_name=posts_table_name,
        upsert=True
    )

if __name__ == '__main__':
    # logger.info(f"Exporting posts from {NEWSLETTER_URL}...")
    # export_newsletter_data(NEWSLETTER_URL)
    #
    # logger.info("Cleaning text and exporting...")
    # export_posts_cleaned_text(
    #     raw_database_name='All posts',
    #     target_database_name='MLAU cleaned text'
    # )
    #
    # logger.info("Exporting data from filtered newsletters...")
    # export_filtered_newsletters(
    #     category_name='Technology',
    #     query='machine learning',
    #     newsletters_table_name='machine_learning_newsletters',
    #     newsletter_limit=10
    # )

    newsletters = supabase_to_df(table_name='machine_learning_newsletters')
    newsletters_list = [Newsletter(url) for url in newsletters['URL'].tolist()]

    logger.info("Exporting data from filtered posts...")
    export_filtered_posts(
        newsletters=newsletters_list,
        query='machine learning',
        posts_table_name='machine_learning_posts',
        post_limit=None
    )