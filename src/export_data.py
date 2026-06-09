"""Save Substack API results to database"""

import datetime
import pandas as pd

from substack_api import Newsletter, Category
from substack_client import (load_newsletter_data, newsletters_to_df,
                             filter_newsletters_in_category, posts_to_df)
from database import save_to_supabase, clear_supabase

# TODO
# * Implement export_category_data function (save to new table?) or keep as API call
# * Function to search all newsletters in a category, returning only the ones related to ML, AI, etc.

def json_serialisable(obj):
    """
    Convert data types that are incompatible with JSON.
    """
    if isinstance(obj, datetime.datetime):
        if pd.isnull(obj):
            return None
        return obj.strftime('%Y-%m-%d %H:%M:%S')
    return obj

def export_newsletter_data() -> None:
    """
    A function to scrape Substack data and store the results in Supabase.
    """
    top_posts, all_posts = load_newsletter_data(
        newsletter_url='https://ameersaleem.substack.com'
    )

    top_posts_df = posts_to_df(top_posts)
    all_posts_df = posts_to_df(all_posts)

    for col in top_posts_df.columns:
        top_posts_df[col] = top_posts_df[col].apply(json_serialisable)

    for col in all_posts_df.columns:
        all_posts_df[col] = all_posts_df[col].apply(json_serialisable)

    save_to_supabase(
        df=top_posts_df.to_dict(orient='records'),
        table_name='Top posts',
        upsert=True
    )
    save_to_supabase(
        df=all_posts_df.to_dict(orient='records'),
        table_name='All posts',
        upsert=True
    )

def export_filtered_category_data(
    category_name: str,
    query: str
) -> None:
    """
    A function that:
    # TODO
    * Makes a call to the Substack API to retrieve the data for the given category
    * Filters the results based on the given query
    * Saves the results in the corresponding Supabase table
    """
    database_table_name = f'{category_name.lower()}_{query.replace(' ', '_')}'
    category = Category(category_name)

    filtered_newsletters = filter_newsletters_in_category(
        category=category,
        query="machine learning",
        limit=10
    )
    filtered_newsletters_df = newsletters_to_df(filtered_newsletters)

    # Make json safe
    for col in filtered_newsletters_df.columns:
        filtered_newsletters_df[col] = filtered_newsletters_df[col].apply(json_serialisable)

    # Save to Supabase
    save_to_supabase(
        df=filtered_newsletters_df.to_dict(orient='records'),
        table_name=database_table_name,
        upsert=True
    )

if __name__ == '__main__':
    export_filtered_category_data('Technology', 'machine learning')