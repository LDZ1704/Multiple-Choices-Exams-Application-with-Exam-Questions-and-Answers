from flask import Flask, render_template, url_for

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

@app.route('/forgot-password')
def forgot_password():
    return(render_template('forgot-password.html'))

@app.route('/subjects')
def subjects():
    return(render_template('subjects.html'))

@app.route('/doing-exam')
def doing_exam():
    return(render_template('doing-exam.html'))

if __name__ == '__main__':
    app.run(debug=True)