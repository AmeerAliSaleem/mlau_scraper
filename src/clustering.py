"""Clustering model and associated functions."""

import numpy as np
import pandas as pd

from substack_api import Post
from text_processing import filter_post_html, clean_text
from settings import STRINGS_TO_REMOVE

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import DBSCAN
from sklearn.decomposition import PCA

import plotly.express as px

from text_processing import vectorise_text

class DBSCAN_model:
    def __init__(self, posts, vectorised_data, model_params):
        self.posts: pd.DataFrame = posts.sort_values(by=['id'], ascending=False)
        self.vectorised_data: np.ndarray = vectorised_data
        self.model_params: dict[str, float] = model_params

        self.core_points = None
        self.labels_ = None
        self.n_clusters_ = None
        self.n_noise_ = None
        self.pca_data = None
        self.df = None
        self.fig = None

    def fit(self):
        dbscan = DBSCAN(**self.model_params)
        dbscan.fit_predict(self.vectorised_data)

        self.core_points = np.zeros_like(dbscan.labels_, dtype=bool)
        self.core_points[dbscan.core_sample_indices_] = True
        self.labels_ = dbscan.labels_

        self.n_clusters_ = len(set(self.labels_)) - (1 if -1 in self.labels_ else 0)
        self.n_noise_ = list(self.labels_).count(-1)

    def pca(self, n_components: int):
        pca = PCA(n_components=n_components)

        self.pca_data = pca.fit_transform(self.vectorised_data)

    def construct_df(self):
        self.df = pd.DataFrame(
            {
                'id': self.posts['id'],
                'title': self.posts['Title'],
                'url': self.posts['URL'],
                'article_number': [len(self.posts) - i for i in range(len(self.posts))],  # Reverse chronological order
                'pca_x': self.pca_data[:, 0],
                'pca_y': self.pca_data[:, 1],
                'cluster_label': self.labels_
            }
        )

        self.df['cluster_label'] = self.df['cluster_label'].astype(str)
        self.df['cluster_label'] = self.df['cluster_label'].apply(
            lambda x: 'outlier' if x == '-1' else x
        )

    def cluster_fig(self, title: str):
        self.fig = px.scatter(
            self.df,
            x='pca_x',
            y='pca_y',
            title=title,
            color='cluster_label',
            custom_data=['article_number', 'title'],
        )
        self.fig.update_traces(
            marker_size=10,
            hovertemplate='Article %{customdata[0]}: %{customdata[1]}<extra></extra>' # extra to remove cluster label on hover
        )

def cluster_text_and_report(
    posts: pd.DataFrame,
    word_embeddings: np.ndarray,
    model_params: dict,
    n_components: int=2,
    plot_title: str="DBSCAN results"
) -> DBSCAN_model:
    """
    A function that:
    - Process the text from a list of Posts
    - Implements DBSCAN on the given data.
    - Stores the clustering results + all other metadata in the DBSCAN_model object.

    Parameters
    ----------
    posts: pd.DataFrame
        The title and URL of each post.
    word_embeddings: np.ndarray
        The embeddings for the text in the posts.
    model_params:
        Parameters for the DBSCAN model.
    n_components: int, optional
        The number of components for PCA. Default is 2.
    plot_title: str, optional
        The title for the clustering plot. Default is "DBSCAN results"

    Returns
    -------
    dbscan: DBSCAN_model
        An object from a custom class that includes the DBSCAN model + metadata.
    """
    dbscan = DBSCAN_model(
        posts=posts,
        vectorised_data=word_embeddings,
        model_params=model_params
    )
    dbscan.fit()
    dbscan.pca(n_components=n_components)
    dbscan.construct_df()
    dbscan.cluster_fig(title=plot_title)

    return dbscan