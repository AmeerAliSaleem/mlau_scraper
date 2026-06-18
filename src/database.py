"""Functions to handle interactions with Supabase"""

import os
import json
import pandas as pd
import logging
from typing import Any
from dotenv import load_dotenv
from supabase import create_client, Client

logger = logging.getLogger(__name__)
load_dotenv()

def get_supabase_client() -> None | Client:
    """
    Create and return Supabase client from environmental variables.

    Returns:
        Supabase client if credentials are available, None otherwise.
    """
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')

    if not url or not key:
        logger.error('Supabase credentials not available')
        return None

    return create_client(url, key)

def access_supabase_data(table_name: str):
    """Retrieve data from the given table."""
    supabase: Client = get_supabase_client()

    logger.info(f'Reading data from {table_name} table...')
    df = (
        supabase.table(table_name)
        .select('*')
        .execute()
    )

    return df

def supabase_to_df(table_name: str) -> pd.DataFrame:
    data_str = access_supabase_data(table_name).model_dump_json()
    data_json = json.loads(data_str)
    data_df = pd.DataFrame(data_json['data'])

    return data_df

def clear_supabase(table_name: str) -> None:
    """Refresh the current state of the 'Top posts' table."""
    supabase: Client = get_supabase_client()

    logger.info(f'Clearing {table_name} table...')
    _ = (
        supabase.table(table_name)
        .delete()
        .neq('id', 0)
        .execute()
    )

def save_to_supabase(
        df: list[dict[str, Any]],
        table_name: str,
        upsert: bool=True,
        on_conflict_col='id'
) -> None:
    """
    Save DataFrame (in json format) to Supabase table.

    Parameters
    ----------
    df: list[dict[str, Any]]
        The data to save.
    table_name: str
        The name of the Supabase table.
    upsert: bool, optional
        Determines whether to perform a standard table insertion,
        or upsert (i.e. updating records that already exist).
        Default value is True
    on_conflict_col: str, optional
        The column(s) to assign upsertion to for uniqueness preservation.
    """
    supabase: Client = get_supabase_client()

    logger.info(f'Saving records to {table_name} table...')

    if upsert:
        _ = (
            supabase.table(table_name)
            .upsert(
                df,
                on_conflict=on_conflict_col
            )
            .execute()
        )
    else:
        _ = (
            supabase.table(table_name)
            .insert(df)
            .execute()
        )

    logger.info(f'Successfully saved records to Supabase')

if __name__ == '__main__':
    get_supabase_client()