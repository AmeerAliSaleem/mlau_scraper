"""Save Substack API results to database"""

import datetime
import pandas as pd
import json

from substack_api import Category
from substack_client import (load_newsletter_data, newsletters_to_df,
                             filter_newsletters_in_category, posts_to_df)
from text_processing import filter_post_html, clean_text
from database import access_supabase_data, save_to_supabase
from settings import STRINGS_TO_REMOVE, NEWSLETTER_URL

# TODO
# - Check that export_filtered_category_data() exports to both tables correctly.
#     - Need to fix issue with duplicates in machine_learning_posts.
#     - Apparently duplicated IDs in the same invocation of save_to_supabase()
# - New table of ML posts related to each ML newsletter.
# - Function to search all newsletters in a category, returning only the ones related to ML, AI, etc.

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
    posts_str = access_supabase_data(table_name=raw_database_name).model_dump_json()
    posts_json = json.loads(posts_str)
    posts_df = pd.DataFrame(posts_json['data'])

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
    newsletters_table_name = f'{category_name.lower()}_{query.replace(' ', '_')}'
    posts_table_name = f'{query.replace(' ', '_')}_posts'
    category = Category(category_name)

    filtered_newsletters, newsletter_to_posts = filter_newsletters_in_category(
        category=category,
        query=query,
        limit=limit
    )

    # --- Exporting query-related posts of the filtered newsletters ---
    for newsletter in newsletter_to_posts:
        newsletter_posts_df = posts_to_df(newsletter_to_posts[newsletter])

        # Make json safe
        for col in newsletter_posts_df.columns:
            newsletter_posts_df[col] = newsletter_posts_df[col].apply(json_serialisable)

        newsletter_posts_df = newsletter_posts_df.fillna('')

        save_to_supabase(
            df=newsletter_posts_df.to_dict(orient='records'),
            table_name=posts_table_name,
            upsert=True
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

# if __name__ == '__main__':
#     export_newsletter_data(NEWSLETTER_URL)

    export_filtered_category_data(
        category_name='Technology',
        query='machine learning',
        limit=1
    )

    # export_posts_cleaned_text(
    #     raw_database_name='All posts',
    #     target_database_name='MLAU cleaned text'
    # )