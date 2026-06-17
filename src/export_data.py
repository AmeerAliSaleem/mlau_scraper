"""Save Substack API results to database"""

import datetime
import pandas as pd
from pandas._libs.missing import NAType

from substack_api import Post, Newsletter, Category
from substack_client import (load_newsletter_data, newsletters_to_df,
                             filter_newsletters_in_category, posts_to_df)
from text_processing import filter_post_html, clean_text
from database import save_to_supabase, clear_supabase
from settings import NEWSLETTER_URL, STRINGS_TO_REMOVE

# TODO
# * Integrate export_filtered_category_data() into webapp
# * Function to search all newsletters in a category, returning only the ones related to ML, AI, etc.

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

def export_newsletter_data(newsletter_url: str) -> None:
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
    posts: list[Post],
    table_name: str
) -> None:
    """
    Cleans text of newsletter's posts and stores the results in the corresponding Supabase table.

    Parameters
    ----------
    posts: list[Post]
        The list of posts.
    table_name: str
        The name of the Supabase table to save the results to.
    """
    posts_text = [
        filter_post_html(
            post=post,
            strings_to_remove=STRINGS_TO_REMOVE
        ) for post in posts
    ]

    posts_text_cleaned = [
        ' '.join(clean_text(text)) for text in posts_text
    ]

    post_ids, post_titles = zip(*[
        (post.get_metadata()['id'], post.get_metadata()['title'])
        for post in posts
    ])

    cleaned_text_df = pd.DataFrame(
        {
            'id': post_ids,
            'Title': post_titles,
            'Cleaned text': posts_text_cleaned
        }
    )

    # Save to Supabase
    save_to_supabase(
        df=cleaned_text_df.to_dict(orient='records'),
        table_name=table_name,
        upsert=True
    )

def export_filtered_category_data(
    category_name: str,
    query: str,
    limit: int=10
) -> None:
    """
    A function that:
    - Makes a call to the Substack API to retrieve the data for the given category
    - Filters the results based on the given query
    - Saves the results in the corresponding Supabase table

    Parameters
    ----------
    category_name: str
        The name of the Substack category to filter on.
    query: str
        The query to filter newsletters on.
    limit: int, optional
        The number of results to return. Default is 10.
    """
    database_table_name = f'{category_name.lower()}_{query.replace(' ', '_')}'
    category = Category(category_name)

    filtered_newsletters = filter_newsletters_in_category(
        category=category,
        query=query,
        limit=limit
    )
    filtered_newsletters_df = newsletters_to_df(filtered_newsletters)

    # Make json safe
    for col in filtered_newsletters_df.columns:
        filtered_newsletters_df[col] = filtered_newsletters_df[col].apply(json_serialisable)

    filtered_newsletters_df = filtered_newsletters_df.fillna('')

    save_to_supabase(
        df=filtered_newsletters_df.to_dict(orient='records'),
        table_name=database_table_name,
        upsert=True
    )

if __name__ == '__main__':
    # top_posts, all_posts = load_newsletter_data("https://ameersaleem.substack.com")
    # all_posts_df = posts_to_df(all_posts)

    export_newsletter_data(newsletter_url=NEWSLETTER_URL)

    # newsletter = Newsletter(NEWSLETTER_URL)
    # all_posts = newsletter.get_posts()
    # export_posts_cleaned_text(
    #     all_posts,
    #     table_name='MLAU cleaned text'
    # )