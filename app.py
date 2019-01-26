from flask import (
    Flask, render_template, request, jsonify, session,
    redirect, url_for
)
from config import *
from game_db_helper import (
    db_create_user, db_create_game, db_update_game_creator,
    db_get_game_users, db_start_game, db_get_game_info,
    db_add_game_word, db_get_game_words, db_get_game_info_from_code,
    db_get_game_completed_game_sentences,
    db_get_game_completed_game_sentences_from_game_code
)
from helper_funcs import is_valid_word

app = Flask(__name__)

app.secret_key = SECRET_KEY


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/create', methods=['GET', 'POST'])
def create_game():
    if request.method == 'GET':
        return render_template('create_game.html')
    else:

        user_name = request.form.get('creator_user_name', 'No Name')
        game_name = request.form.get('game_name', 'No Name')
        number_of_sentences = request.form.get('number_of_sentences', 1)
        words_shown = request.form.get('words_shown', 3)

        new_game_id = db_create_game(game_name, number_of_sentences, words_shown)
        session['game_id'] = new_game_id

        new_user_id = db_create_user(user_name, new_game_id)
        session['user_id'] = new_user_id

        db_update_game_creator(new_game_id, new_user_id)

        return jsonify({'status': 'success'})


@app.route('/join', methods=['GET', 'POST'])
def join_game():
    if request.method == "GET":
        return render_template('game/join.html')
    else:
        user_name = request.form.get('user_name', 'No Name')
        game_code = request.form.get('game_code', None)
        game_info_ = db_get_game_info_from_code(game_code)
        new_user_id = db_create_user(user_name, game_info_['game_id'])

        if new_user_id != 0:

            session['game_id'] = game_info_['game_id']
            session['user_id'] = new_user_id

            return jsonify({'status': 'success'})
        else:
            return jsonify({'status': 'failure'})


@app.route('/join/<string:code>')
def join_game_w_code(code):

    game_info_ = db_get_game_info_from_code(code)

    game_name = game_info_['game_name']

    is_started = True if game_info_['game_started'] else False

    return render_template(
        'game/join.html',
        code=code,
        name=game_name,
        is_started=is_started
    )


@app.route('/game/start', methods=['GET', 'POST'])
def game_start():
    if request.method == 'GET':
        game_id = session.get('game_id', None)
        user_id = session.get('user_id', None)

        game_info_ = db_get_game_info(user_id, game_id)
        is_creator = game_info_['is_creator']
        game_code = game_info_['game_code']

        return render_template(
            'game/start.html', is_creator=is_creator, game_code=game_code)
    else:
        db_start_game(session.get('game_id', None))
        return jsonify({'status': 'success'})


@app.route('/game/on')
def game_on():
    return render_template('game/on.html')


@app.route('/game/end')
def game_end():
    user_id = session.get('user_id', None)
    game_id = session.get('game_id', None)
    word_info = db_get_game_completed_game_sentences(game_id)
    game_info_ = db_get_game_info(user_id, game_id)
    return render_template(
        'game/end.html',
        word_info=word_info,
        game_name=game_info_['game_name'],
        game_code=game_info_['game_code']
    )


@app.route('/game/end/<string:code>')
def game_end_w_code(code):
    word_info = db_get_game_completed_game_sentences_from_game_code(code)
    game_info_ = db_get_game_info_from_code(code)
    return render_template(
        'game/end.html',
        word_info=word_info,
        game_name=game_info_['game_name'],
        game_code=game_info_['game_code']
    )


@app.route('/game/word_list')
def game_word_list():
    game_id = session.get('game_id', None)
    user_id = session.get('user_id', None)

    game_info_ = db_get_game_info(user_id, game_id)

    if game_info_['is_current_user']:
        return jsonify({'status': 'success', 'words': db_get_game_words(game_id)})

    return jsonify({'status': 'failure'})


@app.route('/game/add_word', methods=['POST'])
def game_add_word():
    game_id = session.get('game_id', None)
    user_id = session.get('user_id', None)
    new_word = request.form.get('next_word', None)

    if not is_valid_word(new_word):
        return jsonify({'status': 'failure'})

    game_info_ = db_get_game_info(user_id, game_id)

    if (
            game_info_['is_current_user'] and
            not game_info_['game_finished'] and
            game_info_['game_started']
    ):
        db_add_game_word(new_word, game_id, user_id)

        return jsonify({'status': 'success'})

    return jsonify({'status': 'failure'})


@app.route('/game/info')
def game_info():
    game_id = session.get('game_id', None)
    user_id = session.get('user_id', None)
    game_info_ = db_get_game_info(user_id, game_id)

    return jsonify(game_info_)


@app.route('/game/users')
def game_users():
    users = db_get_game_users(session.get('game_id', None))
    return render_template('game/users.html', users=users)


@app.route('/clear')
def clear():
    session_keys = [x for x in session.keys()]
    for key in session_keys:
        del session[key]
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=DEBUG)
