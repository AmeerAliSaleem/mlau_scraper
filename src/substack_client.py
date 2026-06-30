"""Functions to interact with the Substack API"""

import pandas as pd
from substack_api import Newsletter, Post, Category

def load_newsletter_data(newsletter_url: str) -> list[Post]:
    """
    Loads data from Substack API on top posts and all posts from the given newsletter.

    Parameters
    ----------
    newsletter_url: str
        The newsletter URL.

    Returns
    ----------
    top_posts, all_posts: tuple[pd.DataFrame, pd.DataFrame]
        DataFrames corresponding to the top posts, as well as all posts in reverse chronological order.
    """
    newsletter = Newsletter(newsletter_url)
    all_posts = newsletter.get_posts(sorting="new")

    return all_posts

def newsletters_to_df(newsletters_metadata: list[dict]) -> pd.DataFrame:
    """
    Takes a list of newsletter metadata (all usually under a common category) and:
    - Sorts the newsletters in descending subscriber order
    - Extracts useful statistics from the given list of newsletters
    - Returns the result as a DataFrame.

    Parameters
    ----------
    newsletters_metadata : list[dict]
        The result of the .get_newsletter_metadata() method applied to a Category object.
        This contains the metadata of each newsletter as its own element of the list.

    Returns
    ----------
    top_newsletters_df: pd.DataFrame
        Useful stats in DataFrame format.
    """
    for newsletter in newsletters_metadata:
        newsletter['freeSubscriberCount'] = int(newsletter['freeSubscriberCount'].replace(',', '') if newsletter['freeSubscriberCount'] is not None else 0)

    sorted_newsletters = sorted(
        newsletters_metadata,
        key=lambda x: x['freeSubscriberCount'],
        reverse=True
    )

    top_newsletters = [
        {
            'id': metadata['id'],
            'Name': metadata['name'],
            'URL': metadata['base_url'],
            'Author': metadata['author_name'],
            'Author handle': metadata['author_handle'],
            'Subscriber count': metadata['freeSubscriberCount'],
            'Newsletter creation date': pd.to_datetime(metadata['created_at']),
            'First post date': pd.to_datetime(metadata['first_post_date']),
            'Last chat post': pd.to_datetime(metadata['last_chat_post_at'])
        }
        for metadata in sorted_newsletters
    ]

    top_newsletters_df = pd.DataFrame(top_newsletters)

    return top_newsletters_df

def filter_newsletters_in_category(
        category: Category,
        query: str,
        newsletter_limit: int=10,
        post_limit: int=1
) -> tuple[list[dict], dict[Newsletter, list[Post]]]:
    """
    Searches the category for newsletters filtered by the given query.

    Parameters
    ----------
    category: Category
        The newsletter category to filter.
    query: str
        The (non-Regex) search query.
    newsletter_limit: int, optional
        The maximum number of newsletters to search the posts of. Default is 10.
    post_limit: int, optional
        The maximum number of query-relevant posts to return for each newsletter.
        Default is 1, the case where we just want to flag ML-related newsletters to handle the posts separately.
    
    Returns
    ----------
    tuple[list[dict], dict[Newsletter, list[Post]]]
        A tuple containing:
        The metadata of each newsletter in a dictionary
        A separate dictionary whose keys correspond to newsletters,
        with the values corresponding to the list of posts matching the query.
    """
    # Filter out invite-only publications to prevent HTTP 403 error
    category_metadata = category.get_newsletter_metadata()
    category_metadata = [
        newsletter for newsletter in category_metadata if not newsletter['invite_only']
    ]
    category_metadata = category_metadata[:newsletter_limit]

    filtered_newsletter_urls = []
    newsletter_to_posts_dict = {}
    for newsletter_dict in category_metadata:
        newsletter_url = newsletter_dict['base_url']
        newsletter = Newsletter(url=newsletter_url)
        filtered_posts = newsletter.search_posts(query=query, limit=post_limit)

        if filtered_posts:
            filtered_newsletter_urls.append(newsletter_url)

            newsletter_to_posts_dict[newsletter] = filtered_posts

    # Filter category metadata based on query results
    filtered_newsletters = list(
        filter(lambda n: n['base_url'] in filtered_newsletter_urls, category_metadata)
    )

    return filtered_newsletters, newsletter_to_posts_dict

def posts_to_df(posts: list[Post]) -> pd.DataFrame:
    """
    Extracts useful statistics from the list of posts of the given newsletter.

    Parameters
    ----------
    posts: list[Post]
        The list of newsletter posts.

    Returns
    ----------
    posts_stats_df: pd.DataFrame
        The DataFrame containing useful statistics from the posts.
    """
    posts_metadata = [post.get_metadata() for post in posts]
    posts_stats = [
        {
            'id': metadata['id'],
            'Newsletter id': metadata['publication_id'],
            'Title': metadata['title'],
            'URL': metadata['canonical_url'],
            'Date of upload': pd.to_datetime(metadata['post_date']),
            'Word count': metadata['wordcount'],
            'Likes': metadata['reaction_count'],
            'Restacks': metadata['restacks'],
            "No. of comments (exc. replies)": metadata['comment_count'] - metadata['child_comment_count'],
            'Post HTML': metadata['body_html']
        }
        for metadata in posts_metadata
    ]

    posts_stats_df = pd.DataFrame(posts_stats)

    return posts_stats_df