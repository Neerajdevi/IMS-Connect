from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Set your secret key for sessions

# Function to get a database connection
def get_db_connection():
    conn = sqlite3.connect('app.db')
    conn.row_factory = sqlite3.Row
    return conn

# Route for the home page
@app.route('/')
def home():
    return render_template('home.html')

# Route to show login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            return redirect(url_for('dashboard'))
        else:
            return 'Invalid credentials, please try again.'
    
    return render_template('login.html')

# Route for user registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
        conn.commit()
        conn.close()

        return redirect(url_for('login'))

    return render_template('register.html')

# Route for submitting an idea
@app.route('/submit_idea', methods=['GET', 'POST'])
def submit_idea():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        user_id = session['user_id']
        
        conn = get_db_connection()
        conn.execute('INSERT INTO ideas (title, description, user_id) VALUES (?, ?, ?)', 
                     (title, description, user_id))
        conn.commit()
        conn.close()
        
        return redirect(url_for('dashboard'))

    return render_template('submit_idea.html')

# Route for voting on ideas
@app.route('/vote-idea', methods=['GET', 'POST'])
def vote_idea():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        idea_id = request.form.get('idea_id')  # Get the selected idea ID
        if idea_id:
            conn = get_db_connection()
            user_id = session['user_id']
            # Ensure that a user can vote only once per idea
            conn.execute('INSERT INTO votes (idea_id, user_id) VALUES (?, ?)', (idea_id, user_id))
            conn.commit()
            conn.close()
            return redirect(url_for('dashboard'))

    conn = get_db_connection()
    ideas = conn.execute('SELECT * FROM ideas').fetchall()
    conn.close()
    return render_template('vote_idea.html', ideas=ideas)

# Route for dashboard to show ideas, votes and vote count
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    user_id = session['user_id']
    ideas = conn.execute('SELECT * FROM ideas').fetchall()
    
    # Count votes for each idea
    vote_counts = {}
    for idea in ideas:
        idea_id = idea['id']
        vote_count = conn.execute('SELECT COUNT(*) FROM votes WHERE idea_id = ?', (idea_id,)).fetchone()[0]
        vote_counts[idea_id] = vote_count
    
    votes = conn.execute('SELECT idea_id FROM votes WHERE user_id = ?', (user_id,)).fetchall()
    conn.close()

    voted_ideas = [vote['idea_id'] for vote in votes]
    
    return render_template('dashboard.html', ideas=ideas, voted_ideas=voted_ideas, vote_counts=vote_counts)

# Route to logout the user
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('home'))

# Main function to run the Flask app
if __name__ == '__main__':
    # Create a database if not exists
    conn = get_db_connection()
    conn.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL, password TEXT NOT NULL)')
    conn.execute('CREATE TABLE IF NOT EXISTS ideas (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, description TEXT NOT NULL, user_id INTEGER, FOREIGN KEY (user_id) REFERENCES users (id))')
    conn.execute('CREATE TABLE IF NOT EXISTS votes (id INTEGER PRIMARY KEY AUTOINCREMENT, idea_id INTEGER, user_id INTEGER, FOREIGN KEY (idea_id) REFERENCES ideas (id), FOREIGN KEY (user_id) REFERENCES users (id))')
    conn.commit()
    conn.close()

    app.run(debug=True)
