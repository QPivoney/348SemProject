from flask import Flask, render_template, request, jsonify, redirect, url_for
import sqlite3
import os

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(__file__), 'basketball.db')

# database extras

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    with get_db() as conn:
        with open(os.path.join(os.path.dirname(__file__), 'schema.sql')) as f:
            conn.executescript(f.read())

# pages

@app.route('/')
def index():
    return redirect(url_for('courts'))

@app.route('/courts')
def courts():
    return render_template('courts.html')

@app.route('/report')
def report():
    return render_template('report.html')

# courts

@app.route('/api/courts', methods=['GET'])
def api_get_courts():
    with get_db() as conn:
        rows = conn.execute('SELECT * FROM Courts ORDER BY name').fetchall()
    return jsonify([dict(r) for r in rows])


@app.route('/api/courts', methods=['POST'])
def api_add_court():
    data = request.get_json()
    name = data.get('name', '').strip()
    location = data.get('location', '').strip()
    indoor = int(data.get('indoor', 1))
    max_players = int(data.get('max_players', 10))
    if not name or not location:
        return jsonify({'error': 'Name and location are required'}), 400
    try:
        with get_db() as conn:
            conn.execute("BEGIN")
            cur = conn.execute(
                'INSERT INTO Courts (name, location, indoor, max_players) VALUES (?, ?, ?, ?)',
                (name, location, indoor, max_players)
            )
            conn.execute("COMMIT")
        return jsonify({'court_id': cur.lastrowid}), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Court name already exists'}), 409

@app.route('/api/courts/<int:court_id>', methods=['PUT'])
def api_update_court(court_id):
    data = request.get_json()
    name = data.get('name', '').strip()
    location = data.get('location', '').strip()
    indoor = int(data.get('indoor', 1))
    max_players = int(data.get('max_players', 10))
    if not name or not location:
        return jsonify({'error': 'Name and location are required'}), 400
    try:
        with get_db() as conn:
            conn.execute("BEGIN")
            conn.execute(
                'UPDATE Courts SET name=?, location=?, indoor=?, max_players=? WHERE court_id=?',
                (name, location, indoor, max_players, court_id)
            )
            conn.execute("COMMIT")
        return jsonify({'ok': True})
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Court name already exists'}), 409


@app.route('/api/courts/<int:court_id>', methods=['DELETE'])
def api_delete_court(court_id):
    with get_db() as conn:
        conn.execute("BEGIN")
        conn.execute('DELETE FROM Courts WHERE court_id = ?', (court_id,))
        conn.execute("COMMIT")
    return jsonify({'ok': True})

# sessions

@app.route('/api/sessions', methods=['GET'])
def api_get_sessions():
    with get_db() as conn:
        rows = conn.execute('''
                            SELECT s.session_id,
                                   s.court_id,
                                   c.name AS court_name,
                                   s.date,
                                   s.start_time,
                                   s.duration,
                                   s.game_type,
                                   (SELECT GROUP_CONCAT(p.name, ', ')
                                    FROM SessionPlayers sp
                                             JOIN Players p ON p.player_id = sp.player_id
                                    WHERE sp.session_id = s.session_id) AS players
                            FROM Sessions s
                                     JOIN Courts c ON c.court_id = s.court_id
                            ORDER BY s.date DESC, s.start_time DESC
                            ''').fetchall()
    return jsonify([dict(r) for r in rows])

@app.route('/api/sessions', methods=['POST'])
def api_add_session():
    data = request.get_json()
    court_id = data.get('court_id')
    date = data.get('date', '').strip()
    start_time = data.get('start_time', '').strip()
    duration = data.get('duration')
    game_type = data.get('game_type', '').strip()
    player_ids = data.get('player_ids', [])
    if not all([court_id, date, start_time, duration, game_type]):
        return jsonify({'error': 'All fields are required'}), 400
    with get_db() as conn:
        conn.execute("BEGIN")
        cur = conn.execute(
            'INSERT INTO Sessions (court_id, date, start_time, duration, game_type) VALUES (?,?,?,?,?)',
            (court_id, date, start_time, duration, game_type)
        )
        sid = cur.lastrowid
        for pid in player_ids:
            conn.execute('INSERT INTO SessionPlayers VALUES (?, ?)', (sid, pid))
        conn.execute("COMMIT")
    return jsonify({'session_id': sid}), 201

@app.route('/api/sessions/<int:session_id>', methods=['PUT'])
def api_update_session(session_id):
    data = request.get_json()
    court_id = data.get('court_id')
    date = data.get('date', '').strip()
    start_time = data.get('start_time', '').strip()
    duration = data.get('duration')
    game_type = data.get('game_type', '').strip()
    player_ids = data.get('player_ids', [])
    if not all([court_id, date, start_time, duration, game_type]):
        return jsonify({'error': 'All fields are required'}), 400
    with get_db() as conn:
        # transaction so they pass or fail together
        conn.execute("BEGIN")
        conn.execute(
            'UPDATE Sessions SET court_id=?, date=?, start_time=?, duration=?, game_type=? WHERE session_id=?',
            (court_id, date, start_time, duration, game_type, session_id)
        )
        conn.execute('DELETE FROM SessionPlayers WHERE session_id = ?', (session_id,))
        for pid in player_ids:
            conn.execute('INSERT INTO SessionPlayers VALUES (?, ?)', (session_id, pid))
        conn.execute("COMMIT")
    return jsonify({'ok': True})

@app.route('/api/sessions/<int:session_id>', methods=['DELETE'])
def api_delete_session(session_id):
    with get_db() as conn:
        conn.execute("BEGIN")
        conn.execute('DELETE FROM Sessions WHERE session_id = ?', (session_id,))
        conn.execute("COMMIT")
    return jsonify({'ok': True})


# players

@app.route('/api/players', methods=['GET'])
def api_get_players():
    with get_db() as conn:
        rows = conn.execute('SELECT * FROM Players ORDER BY name').fetchall()
    return jsonify([dict(r) for r in rows])


@app.route('/api/players', methods=['POST'])
def api_add_player():
    data = request.get_json()
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    age = data.get('age')
    skill = data.get('skill_level', '').strip()
    if not name or not email:
        return jsonify({'error': 'Name and email are required'}), 400
    try:
        with get_db() as conn:
            conn.execute("BEGIN")
            cur = conn.execute(
                'INSERT INTO Players (name, email, age, skill_level) VALUES (?, ?, ?, ?)',
                (name, email, age, skill)
            )
            conn.execute("COMMIT")
        return jsonify({'player_id': cur.lastrowid}), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Email already exists'}), 409

@app.route('/api/players/<int:player_id>', methods=['PUT'])
def api_update_player(player_id):
    data = request.get_json()
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    age = data.get('age')
    skill = data.get('skill_level', '').strip()
    if not name or not email:
        return jsonify({'error': 'Name and email are required'}), 400
    try:
        with get_db() as conn:
            conn.execute("BEGIN")
            conn.execute(
                'UPDATE Players SET name=?, email=?, age=?, skill_level=? WHERE player_id=?',
                (name, email, age, skill, player_id)
            )
            conn.execute("COMMIT")
        return jsonify({'ok': True})
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Email already exists'}), 409

@app.route('/api/players/<int:player_id>', methods=['DELETE'])
def api_delete_player(player_id):
    with get_db() as conn:
        conn.execute("BEGIN")
        conn.execute('DELETE FROM Players WHERE player_id = ?', (player_id,))
        conn.execute("COMMIT")
    return jsonify({'ok': True})


# reports

@app.route('/api/report', methods=['GET'])
def api_report():
    player_id = request.args.get('player_id')
    min_dur = request.args.get('min_duration')
    max_dur = request.args.get('max_duration')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    game_type = request.args.get('game_type')

    # avoids duplicate rows
    query = '''
            SELECT s.session_id, 
                   c.name AS court_name, 
                   s.date, 
                   s.start_time,
                   s.duration, 
                   s.game_type,
                   (SELECT GROUP_CONCAT(p.name, ', ')
                    FROM SessionPlayers sp
                             JOIN Players p ON p.player_id = sp.player_id
                    WHERE sp.session_id = s.session_id) AS players,
                   (SELECT COUNT(*)
                    FROM SessionPlayers sp
                    WHERE sp.session_id = s.session_id) AS player_count
            FROM Sessions s JOIN Courts c ON c.court_id = s.court_id 
            '''

    conditions = []
    params = []

    if player_id:
        conditions.append('s.session_id IN (SELECT session_id FROM SessionPlayers WHERE player_id = ?)')
        params.append(player_id)
    if min_dur:
        conditions.append('s.duration >= ?')
        params.append(min_dur)
    if max_dur:
        conditions.append('s.duration <= ?')
        params.append(max_dur)
    if date_from:
        conditions.append('s.date >= ?')
        params.append(date_from)
    if date_to:
        conditions.append('s.date <= ?')
        params.append(date_to)
    if game_type:
        conditions.append('s.game_type = ?')
        params.append(game_type)

    if conditions:
        query += ' WHERE ' + ' AND '.join(conditions)

    query += ' ORDER BY s.date DESC, s.start_time DESC'

    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()
        rows = [dict(r) for r in rows]

        stats = {}
        if rows:
            durations = [r['duration'] for r in rows]
            player_counts = [r['player_count'] for r in rows]
            stats = {
                'total_sessions': len(rows),
                'avg_duration': round(sum(durations) / len(durations), 1),
                'min_duration': min(durations),
                'max_duration': max(durations),
                'avg_players': round(sum(player_counts) / len(player_counts), 1),
                'total_time': sum(durations),
            }

    return jsonify({'sessions': rows, 'stats': stats})


# run

init_db()

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
