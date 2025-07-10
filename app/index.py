from app import app
from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return(render_template('index.html'))

@app.route('/login')
def login():
    return(render_template('login.html'))

@app.route('/register')
def register():
    return(render_template('register.html'))

@app.route('/examdetail')
def exam_detail():
    return(render_template('examdetail.html'))

@app.route('/account')
def account_detail():
    return(render_template('account.html'))

if __name__ == '__main__':
    app.run(debug=True)