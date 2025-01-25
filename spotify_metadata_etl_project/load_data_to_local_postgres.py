# load raw json data into local postgres and normalise the data
# should be a one-off script then postgres will be connected to rds
# to make sure everything follows IaC principles, will need to write a script for the connection
# data here will act as OLTP data

import json
import os
from datetime import datetime

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


# def create_tables(conn):
#     with conn.cursor() as cur:
#         cur.execute("DROP TABLE IF EXISTS playlists CASCADE;")
#
#         cur.execute("""
#             CREATE TABLE IF NOT EXISTS playlists (
#                 playlist_id SERIAL PRIMARY KEY,
#                 name TEXT NOT NULL,
#                 collaborative BOOLEAN,
#                 modified_at TIMESTAMP,
#                 num_tracks INT,
#                 num_albums INT,
#                 num_followers INT,
#                 duration_ms BIGINT,
#                 num_artists INT
#             );
#         """)
#         conn.commit()


def with_cursor(func):
    def wrapper(conn, *args, **kwargs):
        with conn.cursor() as cur:
            result = func(cur, *args, **kwargs)
            conn.commit()
            return result

    return wrapper


@with_cursor
def create_playlist_table(cur):
    cur.execute("DROP TABLE IF EXISTS playlists CASCADE;")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS playlists (
            playlist_id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            collaborative BOOLEAN,
            modified_at TIMESTAMP,
            num_tracks INT,
            num_albums INT,
            num_followers INT,
            duration_ms BIGINT,
            num_artists INT
        );
    """)


def validate_playlist(playlist):
    required_fields = [
        "name",
        "collaborative",
        "modified_at",
        "num_tracks",
        "num_albums",
        "num_followers",
        "duration_ms",
        "num_artists",
    ]

    missing_fields = [field for field in required_fields if field not in playlist]
    if missing_fields:
        raise ValueError(f"Missing required fields: {missing_fields}")

    if not isinstance(playlist["name"], str):
        raise ValueError("Playlist name must be a string")

    if not isinstance(playlist["collaborative"], bool):
        try:
            playlist["collaborative"] = convert_to_boolean(playlist["collaborative"])
        except ValueError:
            raise Exception("Failed to convert to boolean") from None

    numeric_fields = ["num_tracks", "num_albums", "num_followers", "duration_ms", "num_artists"]
    for field in numeric_fields:
        if not isinstance(playlist[field], int | float) or playlist[field] < 0:
            raise ValueError(f"{field} must be a non-negative number")

    if len(playlist["tracks"]) != playlist["num_tracks"]:
        raise ValueError(
            f"Track count mismatch: num_tracks={playlist['num_tracks']} but found {len(playlist['tracks'])} tracks"
        )

    album_set = {track["album_uri"] for track in playlist["tracks"]}
    if len(album_set) != playlist["num_albums"]:
        raise ValueError(
            f"Album count mismatch: num_albums={playlist['num_albums']} but found {len(album_set)} unique albums"
        )

    artist_set = {track["artist_uri"] for track in playlist["tracks"]}
    if len(artist_set) != playlist["num_artists"]:
        raise ValueError(
            f"Artist count mismatch: num_artists={playlist['num_artists']} but found {len(artist_set)} unique artists"
        )


@with_cursor
def upsert_playlist(cur, playlist):
    cur.execute(
        """
        INSERT INTO playlists (
            name, collaborative, modified_at, num_tracks,
            num_albums, num_followers, duration_ms, num_artists
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        """,
        (
            playlist["name"],
            convert_to_boolean(playlist["collaborative"]),
            datetime.fromtimestamp(playlist["modified_at"]),
            playlist["num_tracks"],
            playlist["num_albums"],
            playlist["num_followers"],
            playlist["duration_ms"],
            playlist["num_artists"],
        ),
    )


def load_data(conn, data):
    if not isinstance(data, dict) or "playlists" not in data:
        raise ValueError(f"Invalid data structure. Expected dict with 'playlists' key. Got: {type(data)}")

    for playlist in data["playlists"]:
        validate_playlist(playlist)
        try:
            upsert_playlist(conn, playlist)
        except Exception as e:
            print(f"Error processing playlist: {playlist.get('name', e)}")
            conn.rollback()
            raise


if __name__ == "__main__":
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        # Note: we pass conn to the decorated function
        create_playlist_table(conn)

        file_list = list_files()
        for file_path in file_list[:2]:
            print(f"Processing file: {file_path}")
            data = get_data(file_path)
            load_data(conn, data)
    except Exception as e:
        import traceback

        print(f"An error occurred: {str(e)}")
        print("Full traceback:")
        print(traceback.format_exc())
    finally:
        if conn:
            conn.close()
