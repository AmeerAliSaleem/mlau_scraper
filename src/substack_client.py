"""Functions to interact with the Substack API"""

import pandas as pd
from substack_api import Newsletter, Post, Category

def load_newsletter_data(
        newsletter_url: str,
        top_limit: int=5
) -> tuple[list[Post], list[Post]]:
    """
    Loads data on top posts and recent posts from the given newsletter.
    """
    newsletter = Newsletter(newsletter_url)
    top_posts = newsletter.get_posts(sorting="top", limit=top_limit)
    recent_posts = newsletter.get_posts(sorting="new")

    return top_posts, recent_posts

def newsletters_to_df(newsletters_metadata: list[dict]) -> pd.DataFrame:
    """
    Extracts useful statistics from the given list of newsletters (all usually under a common category).
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

def posts_to_df(posts: list[Post]) -> pd.DataFrame:
    """
    Extracts useful statistics from the list of posts of the given newsletter.
    """
    top_titles_metadata = [post.get_metadata() for post in posts]
    top_titles = [
        {
            'id': metadata['id'],
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