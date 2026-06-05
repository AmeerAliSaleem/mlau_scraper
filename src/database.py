import os
import logging
from supabase import create_client, Client

logger = logging.getLogger(__name__)

def get_supabase_client():
    """
    Create and return Supabase client from environmental variables.

    Returns:
        Supabase client if credentials are available, None otherwise.
    """
    url = os.environ.get('SUPABASE_URL')
    key = os.environ.get('SUPABASE_KEY')

    if not url or not key:
        logger.error('Supabase credentials not available')
        return None

    return create_client(url, key)

def access_supabase_data():
    pass

def save_to_supabase(df, table_name):
    supabase: Client = get_supabase_client()
    if supabase is None:
        raise ValueError("Supabase client not available. Missing environmental variables SUPABASE_URL and/or SUPABASE_KEY")

    logger.info('Saving predictions to Supabase...')
    response = (
        supabase.table(table_name)
        .insert(df)
        .execute()
    )

    logger.info(f'Successfully saved prediction to Supabase')

if __name__ == '__main__':
    get_supabase_client()