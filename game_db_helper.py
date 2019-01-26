import mysql.connector
from mysql.connector import errorcode
from db import get_conn_cursor
from string import digits
import random


def db_create_user(name, game_id):
    conn, cursor = get_conn_cursor()

    cursor.execute(
        """
            INSERT INTO game.users
            (name, game_id)
            SELECT t.name, t.game_id FROM (SELECT %s name, %s game_id) t
            JOIN game.status s
            ON t.game_id = s.game_id
            WHERE s.started != 1
        """,
        (name, game_id)
    )
    user_id = cursor.getlastrowid()

    conn.close()

    return user_id


def db_create_game(name, numb_sentences, words_shown):
    conn, cursor = get_conn_cursor()

    cursor.execute(
        """
            INSERT INTO game.game
            (name, sentences, words_shown) 
            VALUES 
            (%s,%s,%s)
        """,
        (name, numb_sentences, words_shown)
    )
    game_id = cursor.getlastrowid()

    # insert a record into game status
    cursor.execute(
        """
            INSERT INTO game.status
            (game_id) 
            VALUES 
            (%s)
        """,
        (game_id,)
    )

    conn.close()

    create_game_code(game_id)

    return game_id


def db_update_game_creator(game_id, user_id):
    conn, cursor = get_conn_cursor()

    cursor.execute(
        """
            UPDATE game.game
            SET creator_id = %s
            WHERE id = %s
        """,
        (user_id, game_id)
    )

    conn.close()


def db_get_game_code(game_id):
    conn, cursor = get_conn_cursor()

    cursor.execute(
        "SELECT code FROM game.codes WHERE game_id = %s",
        (game_id,)
    )
    game_code = cursor.fetchone()['code']

    conn.close()

    return game_code


def create_game_code(game_id):
    conn, cursor = get_conn_cursor()
    while 1:
        code = generate_game_code()

        try:
            cursor.execute(
                """
                    INSERT INTO game.codes
                    (game_id, code) 
                    VALUES (%s,%s)
                """,
                (game_id, code)
            )

            conn.close()

            break
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_DUP_INDEX:
                pass
            else:
                raise err


def db_get_game_users(game_id, with_user_id=False):
    conn, cursor = get_conn_cursor()

    cursor.execute(
        """
            SELECT 
                u.name name,
                IF(g.creator_id = u.id, true, false) creator,
                u.id user_id
            FROM game.users u
            LEFT JOIN game.game g
            ON g.id = u.game_id
            WHERE game_id = %s
        """,
        (game_id,)
    )

    users = []

    for x in cursor.fetchall():
        d = {
            'name': x['name'],
            'is_creator': x['creator']
        }
        if with_user_id:
            d['user_id'] = x['user_id']
        users.append(d)

    conn.close()

    return users


def db_start_game(game_id):
    conn, cursor = get_conn_cursor()

    cursor.execute(
        """
            UPDATE game.status
            SET started = 1, date_started = NOW()
            WHERE game_id = %s
        """,
        (game_id,)
    )

    conn.close()

    db_set_game_order(game_id)


def db_set_game_order(game_id):
    user_ids = [x['user_id'] for x in db_get_game_users(game_id, True)]

    random.shuffle(user_ids)

    conn, cursor = get_conn_cursor()

    for i, user_id in enumerate(user_ids, 1):
        cursor.execute(
            """
                INSERT INTO game.`order`
                (game_id, user_id, `order`) 
                VALUES 
                (%s, %s, %s)
            """,
            (game_id, user_id, i)
        )

    cursor.execute(
        """
            UPDATE game.status
            SET current_user_id = %s
            WHERE game_id = %s
        """,
        (user_ids[0], game_id)
    )

    conn.close()


def db_add_game_word(word, game_id, user_id):
    conn, cursor = get_conn_cursor()

    cursor.execute(
        """
            INSERT INTO game.words
            (game_id, user_id, word)
            VALUES 
            (%s, %s, %s)
        """,
        (game_id, user_id, word)
    )

    if word.endswith('.'):
        cursor.execute(
            """
                UPDATE game.status
                SET sentences_completed = sentences_completed + 1
                WHERE game_id = %s
            """,
            (game_id,)
        )

    next_user_id = db_get_next_user_in_order(game_id)

    cursor.execute(
        """
            UPDATE game.status
            SET current_user_id = %s
            WHERE game_id = %s
        """,
        (next_user_id, game_id)
    )

    cursor.execute(
        """
            SELECT 
                s.sentences_completed as sentences_completed,
                g.sentences sentences
            FROM game.status s
            LEFT JOIN game.game g
            ON g.id = s.game_id
            WHERE game_id = %s
        """,
        (game_id,)
    )

    result = cursor.fetchone()

    sentences_completed = result['sentences_completed']
    game_sentences = result['sentences']

    if int(sentences_completed) >= int(game_sentences):
        cursor.execute(
            """
                UPDATE game.status
                SET finished = 1, date_finished = NOW()
                WHERE game_id = %s
            """,
            (game_id,)
        )

    conn.close()


def db_get_next_user_in_order(game_id):
    """
    Gets the next user based on the order.

    :param str|int game_id: The game ID
    :return: The ID of the next user
    """
    conn, cursor = get_conn_cursor()

    cursor.execute(
        """
            SELECT current_user_id
            FROM game.status
            WHERE game_id = %s
        """,
        (game_id,)
    )

    current_user_id = cursor.fetchone()['current_user_id']

    cursor.execute(
        """
            SELECT user_id
            FROM game.`order`
            WHERE game_id = %s
            ORDER BY `order` ASC
        """,
        (game_id,)
    )

    user_order = []
    for x in cursor.fetchall():
        user_order.append(x['user_id'])

    conn.close()

    for i, x in enumerate(user_order):
        if x == current_user_id:
            if i + 1 == len(user_order):
                return user_order[0]
            return user_order[i + 1]


def db_get_game_info(user_id, game_id):
    conn, cursor = get_conn_cursor()

    cursor.execute(
        """
            SELECT 
                g.id game_id,
                started game_started,
                finished game_finished,
                IF(s.current_user_id = %(user_id)s, true, false) is_current_user,
                u2.name current_user_name,
                IF(g.creator_id = %(user_id)s, true, false) is_creator,
                g.name game_name,
                c.code game_code,
                IF(u1.id = %(user_id)s, true, false) is_user,
                s.sentences_completed sentences_completed
            FROM
            game.game g
            LEFT JOIN game.users u1
            ON g.id = u1.game_id AND u1.id = %(user_id)s
            LEFT JOIN game.status s
            ON g.id = s.game_id
            LEFT JOIN game.users u2
            ON g.id = u2.game_id AND u2.id = s.current_user_id
            LEFT JOIN game.`order` o
            ON g.id = o.game_id
            LEFT JOIN game.codes c
            ON g.id = c.game_id
            WHERE
                g.id = %(game_id)s
        """,
        {
            'game_id': game_id,
            'user_id': user_id
        }
    )

    game_info = cursor.fetchone()

    conn.close()

    return game_info


def db_get_game_info_from_code(game_code):
    conn, cursor = get_conn_cursor()

    cursor.execute(
        """
            SELECT game_id
            FROM game.codes
            WHERE code = %s
        """,
        (game_code,)
    )

    game_id = cursor.fetchone()['game_id']

    conn.close()

    return db_get_game_info(None, game_id)


def db_get_game_words(game_id):
    conn, cursor = get_conn_cursor()

    cursor.execute(
        """
            SELECT words_shown FROM game.game
            WHERE id = %s
        """,
        (game_id,)
    )

    words_shown = cursor.fetchone()['words_shown']

    cursor.execute(
        """
            SELECT 
                w.word word
            FROM game.words w
            LEFT JOIN game.game g
            ON g.id = w.game_id
            WHERE g.id = %s
            ORDER BY w.date_added DESC
            LIMIT %s
        """,
        (game_id, words_shown)
    )

    words = []
    for x in cursor.fetchall():
        words.append(x['word'])

    conn.close()

    words.reverse()

    return words


def db_get_completed_game_sentences(game_id):
    conn, cursor = get_conn_cursor()

    cursor.execute(
        """
            SELECT
                w.word word,
                u.name user_name
            FROM game.words w
            LEFT JOIN game.users u
            ON u.id = w.user_id
            WHERE w.game_id = %s
            ORDER BY w.date_added
        """,
        (game_id,)
    )

    word_info = cursor.fetchall()

    conn.close()

    return word_info


def db_get_completed_game_sentences_from_code(game_code):
    conn, cursor = get_conn_cursor()

    cursor.execute(
        """
            SELECT game_id
            FROM game.codes
            WHERE code = %s
        """,
        (game_code,)
    )

    game_id = cursor.fetchone()['game_id']

    conn.close()

    return db_get_completed_game_sentences(game_id)


def generate_game_code():
    return ''.join([random.choice(digits) for _ in range(6)])
