# mlau_scraper

Current build status (via CircleCI):

[![CircleCI](https://dl.circleci.com/status-badge/img/circleci/JBgmi7TTaucEpa7BcKTbDS/SE6taGMQh95prYoW5ScJ2h/tree/main.svg?style=svg)](https://dl.circleci.com/status-badge/redirect/circleci/JBgmi7TTaucEpa7BcKTbDS/SE6taGMQh95prYoW5ScJ2h/tree/main)

A tool to extract insights from my [Machine Learning Algorithms Unpacked publication](https://ameersaleem.substack.com/), with the aim of exploring what content resonates with the audience, what doesn't, and recommendations on future topics that I should write about.

The dashboard is live on Streamlit Community Cloud, linked [here](https://mlau-analysis.streamlit.app/).

# Components
## 1. Substack API call results saved to Supabase

The information on newsletters and their posts are accessed via the (unofficial) [Substack API](https://github.com/nhagar/substack_api). These results are then saved to Supabase tables, which the live dashboard reads from.

## 2. DBSCAN clustering

Investigation of the natural groupings of my posts, as well as outliers uncovered by DBSCAN and whether this correlates with top posts. The dashboard also allows users to train a DBSCAN model with their own choice of hyperparameters, with the results displayed.

## 3. EDA on Substack posts

The dashboard provides options for EDA, including word count, hour of upload and top word frequency by article.

## 4. (TBA) Comparison with other newsletters

Comparison of EDA with the posts of other ML-related newsletters to understand audience preferences in the ML content creation space.

# How to run webapp

The dashboard is already live at [this link](https://mlau-analysis.streamlit.app/).

This project manages Python packages and their dependencies with [uv](https://docs.astral.sh/uv/).

To run the webapp locally, assuming uv is installed:
- Clone the repository
- Navigate to the root of the local project repository in the terminal and run
    ```commandline
    uv venv
    ```
  and then
    ```commandline
    uv sync
    ```
    to create the virtual environment called `.venv` and install all the project dependencies in it respectively.
- To run the webapp locally, run
    ```commandline
    streamlit run src/dashboard.py
    ```
  or, with Make installed, you can instead use
  ```commandline
  make dashboard
  ```

# To Develop
- Step 4
- Continuous Deployment w/ GitHub Actions. This would involve calling the functions in `export_data.py` every week to update my newest Substack post and those of other ML-related newsletters.
- Complete testing functions in the 'tests' folder
- MLOps for DBSCAN/extension to HDBSCAN