# load raw json data into local postgres and normalise the data
# should be a one-off script then postgres will be connected to rds
# to make sure everything follows IaC principles, will need to write a script for the connection
# data here will act as OLTP data

import json
import os

import psycopg2

path = "spotify_metadata_etl_project/data/"

DB_CONFIG = {
    "dbname": "spotify_ingestion_db",
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": "postgres",
    "port": 5432,
}


def list_files(path=path):
    return os.listdir(path)


def get_data(file, path=path):
    with open(path + file) as f:
        data = json.load(f)
    return data


def convert_to_boolean(value):
    if isinstance(value, str):
        return value.lower() == "true"
    return bool(value)


def with_cursor(func):
    def wrapper(conn, *args, **kwargs):
        with conn.cursor() as cur:
            result = func(cur, *args, **kwargs)
            conn.commit()
            return result

    return wrapper


@with_cursor
def count_rows(cur):
    cur.execute("SELECT COUNT(*) FROM playlists;")
    return cur.fetchone()[0]


@with_cursor
def upsert_playlist(cur, playlist):
    try:
        tracks_json = json.dumps(playlist["tracks"])
        cur.execute(
            """
            INSERT INTO playlists (playlist_id, name, collaborative, modified_at, num_tracks, num_albums,
            num_followers, duration_ms, num_artists, num_edits, tracks)
            VALUES (%s, %s, %s::boolean, to_timestamp(%s), %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (playlist_id) DO UPDATE SET
                name = EXCLUDED.name,
                collaborative = EXCLUDED.collaborative,
                modified_at = EXCLUDED.modified_at,
                num_tracks = EXCLUDED.num_tracks,
                num_albums = EXCLUDED.num_albums,
                num_followers = EXCLUDED.num_followers,
                duration_ms = EXCLUDED.duration_ms,
                num_artists = EXCLUDED.num_artists,
                num_edits = EXCLUDED.num_edits,
                tracks = EXCLUDED.tracks;
        """,
            (
                playlist["pid"],
                playlist["name"],
                convert_to_boolean(playlist["collaborative"]),
                playlist["modified_at"],
                playlist["num_tracks"],
                playlist["num_albums"],
                playlist["num_followers"],
                playlist["duration_ms"],
                playlist["num_artists"],
                playlist["num_edits"],
                tracks_json,
            ),
        )
    except Exception as e:
        print(f"Error inserting playlist: {e}")
        raise


@with_cursor
def create_table(cur):
    cur.execute("""
        CREATE TABLE IF NOT EXISTS playlists (
            playlist_id TEXT PRIMARY KEY,
            name TEXT,
            collaborative BOOLEAN,
            modified_at TIMESTAMP,
            num_tracks INTEGER,
            num_albums INTEGER,
            num_followers INTEGER,
            duration_ms INTEGER,
            num_artists INTEGER,
            num_edits INTEGER,
            tracks JSONB
        )
    """)


@with_cursor
def drop_table(cur):
    cur.execute("""
        DROP TABLE IF EXISTS playlists;
    """)
    print("dropped table")


if __name__ == "__main__":
    conn = psycopg2.connect(**DB_CONFIG)

    file_list = list_files()
    drop_table(conn)
    create_table(conn)

    for file_path in file_list[:5]:
        print(f"Processing file: {file_path}")
        data = get_data(file_path)
        playlists = data["playlists"]
        for playlist in playlists:
            upsert_playlist(conn, playlist)
        print(f"counting number of rows: {count_rows(conn)}")
