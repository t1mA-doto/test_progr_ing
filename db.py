import sqlite3
import config

connection = None


def get_db():
    global connection
    if not connection:
        connection = sqlite3.connect(
            config.DATABASE_NAME,
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        connection.row_factory = sqlite3.Row

    return connection


def close_db():
    if connection is not None:
        connection.close()


