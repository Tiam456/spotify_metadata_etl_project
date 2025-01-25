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


def create_tables(conn):
    with conn.cursor() as cur:
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
        # cur.execute("""
        #     CREATE TABLE IF NOT EXISTS artists (
        #         artist_id SERIAL PRIMARY KEY,
        #         artist_name TEXT NOT NULL,
        #         artist_uri TEXT NOT NULL UNIQUE
        #     );
        # """)
        # cur.execute("""
        #     CREATE TABLE IF NOT EXISTS albums (
        #         album_id SERIAL PRIMARY KEY,
        #         album_name TEXT NOT NULL,
        #         album_uri TEXT NOT NULL UNIQUE
        #     );
        # """)
        # cur.execute("""
        #     CREATE TABLE IF NOT EXISTS tracks (
        #         track_id SERIAL PRIMARY KEY,
        #         track_name TEXT NOT NULL,
        #         track_uri TEXT NOT NULL UNIQUE,
        #         duration_ms BIGINT,
        #         album_id INT REFERENCES albums(album_id),
        #         CONSTRAINT fk_album FOREIGN KEY (album_id) REFERENCES albums(album_id)
        #     );
        # """)
        # cur.execute("""
        #     CREATE TABLE IF NOT EXISTS track_artists (
        #         track_id INT,
        #         artist_id INT,
        #         PRIMARY KEY (track_id, artist_id),
        #         CONSTRAINT fk_track FOREIGN KEY (track_id) REFERENCES tracks(track_id),
        #         CONSTRAINT fk_artist FOREIGN KEY (artist_id) REFERENCES artists(artist_id)
        #     );
        # """)
        # cur.execute("""
        #     CREATE TABLE IF NOT EXISTS playlist_tracks (
        #         playlist_id INT,
        #         track_id INT,
        #         PRIMARY KEY (playlist_id, track_id),
        #         CONSTRAINT fk_playlist FOREIGN KEY (playlist_id) REFERENCES playlists(playlist_id),
        #         CONSTRAINT fk_track FOREIGN KEY (track_id) REFERENCES tracks(track_id)
        #     );
        # """)

        conn.commit()


# def upsert_artist(cur, artist_name, artist_uri):
#     cur.execute("""
#         INSERT INTO artists (artist_name, artist_uri)
#         VALUES (%s, %s)
#         ON CONFLICT (artist_uri) DO UPDATE
#         SET artist_name = EXCLUDED.artist_name
#         RETURNING artist_id;
#     """, (artist_name, artist_uri))
#     return cur.fetchone()[0]

# def upsert_album(cur, album_name, album_uri):
#     cur.execute("""
#         INSERT INTO albums (album_name, album_uri)
#         VALUES (%s, %s)
#         ON CONFLICT (album_uri) DO UPDATE
#         SET album_name = EXCLUDED.album_name
#         RETURNING album_id;
#     """, (album_name, album_uri))
#     return cur.fetchone()[0]

# def upsert_track(cur, track_name, track_uri, duration_ms, album_id):
#     cur.execute("""
#         INSERT INTO tracks (track_name, track_uri, duration_ms, album_id)
#         VALUES (%s, %s, %s, %s)
#         ON CONFLICT (track_uri) DO UPDATE
#         SET track_name = EXCLUDED.track_name,
#             duration_ms = EXCLUDED.duration_ms,
#             album_id = EXCLUDED.album_id
#         RETURNING track_id;
#     """, (track_name, track_uri, duration_ms, album_id))
#     return cur.fetchone()[0]


def load_data(conn, data):
    with conn.cursor() as cur:
        # Add check for data structure
        if not isinstance(data, dict) or "playlists" not in data:
            raise ValueError(f"Invalid data structure. Expected dict with 'playlists' key. Got: {type(data)}")

        for playlist in data["playlists"]:
            try:
                cur.execute(
                    """
                    INSERT INTO playlists (
                        name, collaborative, modified_at, num_tracks,
                        num_albums, num_followers, duration_ms, num_artists
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING playlist_id;
                """,
                    (
                        playlist["name"],
                        playlist["collaborative"],
                        datetime.fromtimestamp(playlist["modified_at"]),
                        playlist["num_tracks"],
                        playlist["num_albums"],
                        playlist["num_followers"],
                        sum(track["duration_ms"] for track in playlist["tracks"]),
                        len({artist["artist_uri"] for track in playlist["tracks"] for artist in track["artists"]}),
                    ),
                )

                # for track in playlist["tracks"]:
                #     # Validate track data
                #     required_track_fields = ["album_name", "album_uri", "track_name",
                #                           "track_uri", "duration_ms", "artists"]
                #     missing_fields = [field for field in required_track_fields if field not in track]
                #     if missing_fields:
                #         raise ValueError(f"Missing required track fields: {missing_fields}")

                # album_id = upsert_album(cur, track["album_name"], track["album_uri"])

                # track_id = upsert_track(
                #     cur,
                #     track["track_name"],
                #     track["track_uri"],
                #     track["duration_ms"],
                #     album_id
                # )

                # for artist in track["artists"]:
                #     if "artist_name" not in artist or "artist_uri" not in artist:
                #         raise ValueError(f"Missing artist data fields. Got: {artist}")

                #     artist_id = upsert_artist(cur, artist["artist_name"], artist["artist_uri"])

                #     cur.execute("""
                #         INSERT INTO track_artists (track_id, artist_id)
                #         VALUES (%s, %s)
                #         ON CONFLICT (track_id, artist_id) DO NOTHING;
                #     """, (track_id, artist_id))

                # cur.execute("""
                #     INSERT INTO playlist_tracks (playlist_id, track_id)
                #     VALUES (%s, %s)
                #     ON CONFLICT (playlist_id, track_id) DO NOTHING;
                # """, (playlist_id, track_id))

            except Exception as e:
                print(f"Error processing playlist: {playlist.get('name', 'Unknown')}")
                print(f"Error details: {str(e)}")
                conn.rollback()
                raise

        conn.commit()


if __name__ == "__main__":
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    try:
        file_list = list_files()
        create_tables(conn)
        for file_path in file_list[:2]:
            data = get_data(file_path)
            load_data(conn, data)
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if conn:
            conn.close()
