import sqlite3
import hashlib
import os
import streamlit as st
import sql
import logic

DB_PATH = os.path.join(os.path.dirname(__file__), 'nea.db')


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


@st.cache_resource
def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('PRAGMA foreign_keys = ON')
    _init_schema(cursor, conn)
    return conn


def _init_schema(cursor, conn):
    sql.createOrgTable(cursor, conn)
    sql.createCoachesTable(cursor, conn)
    sql.createTeamsTable(cursor, conn)
    sql.createPlayersTable(cursor, conn)
    sql.createMatchesTable(cursor, conn)
    sql.createPlayerTeamLinkTable(cursor, conn)
    sql.createCoachTeamLinkTable(cursor, conn)
    for positionName in logic.positionsList:
        sql.createPositionTable(cursor, conn, positionName)

    # Extra columns the original schema didn't have but a real deployment needs.
    _add_column_if_missing(cursor, conn, 'Players', 'Injured', 'BOOLEAN DEFAULT 0')
    _add_column_if_missing(cursor, conn, 'Players', 'MustResetPassword', 'BOOLEAN DEFAULT 1')
    _add_column_if_missing(cursor, conn, 'Coaches', 'MustResetPassword', 'BOOLEAN DEFAULT 1')
    _add_column_if_missing(cursor, conn, 'Matches', 'HomeAway', 'STRING')


def _add_column_if_missing(cursor, conn, table, column, coltype):
    cursor.execute("PRAGMA table_info({})".format(table))
    cols = [row[1] for row in cursor.fetchall()]
    if column not in cols:
        cursor.execute('ALTER TABLE {} ADD COLUMN {} {}'.format(table, column, coltype))
        conn.commit()


def cur_conn():
    conn = get_connection()
    return conn.cursor(), conn
