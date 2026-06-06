"""Save Substack API results to database"""
import datetime

from substack_client import load_newsletter_data, newsletters_to_df, posts_to_df
from database import save_to_supabase, clear_supabase

# TODO
# * Implement export_category_data function (save to new table?)

def json_serialisable(obj):
    """
    Convert data types that are incompatible with JSON.
    """
    if isinstance(obj, datetime.datetime):
        return obj.strftime('%Y-%m-%d %H:%M:%S')
    return obj

def export_newsletter_data() -> None:
    """
    A function to scrape Substack data and store the results in Supabase.
    """
    top_posts, recent_posts = load_newsletter_data(
        newsletter_url='https://ameersaleem.substack.com'
    )

    top_posts_df = posts_to_df(top_posts)
    recent_posts_df = posts_to_df(recent_posts)

    for col in top_posts_df.columns:
        top_posts_df[col] = top_posts_df[col].apply(json_serialisable)

    for col in recent_posts_df.columns:
        recent_posts_df[col] = recent_posts_df[col].apply(json_serialisable)

    save_to_supabase(
        df=top_posts_df.to_dict(orient='records'),
        table_name='Top posts',
        upsert=True
    )
    save_to_supabase(
        df=recent_posts_df.to_dict(orient='records'),
        table_name='All posts',
        upsert=True
    )

def export_category_data():
    pass

if __name__ == '__main__':
    export_newsletter_data()