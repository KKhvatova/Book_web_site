from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from models import *

app = Flask(__name__)

ENV = 'dev'

if ENV == 'dev':
    app.debug = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:123456@127.0.0.3/book_user'
else:
    app.debug = False
    app.config['SQLALCHEMY_DATABASE_URI'] = ''

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

#db.init_app(app)
#with app.app_context():
#    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route("/sing_in", methods=['POST'])
def sing_in(): 
    '''sing in if you are have account'''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        #print(username, password)
        if username == '' or password == '':
            return render_template('index.html', message='Please enter required fields')
        if db.session.query(User).filter(User.username == username, User.password == password).count() == 0:
            return render_template('index.html', message ='The email or password you entered is invalid')
        return render_template('more.html')


@app.route("/register")
def register():
    return render_template('index_2.html')

@app.route("/sing_up", methods=["POST"])
def sing_up():
    '''Create an accout'''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        re_password = request.form['re_password']
        #print(username, password)
        if username == '' or password == '' or re_password == '':
            return render_template('index_2.html', message='Please enter required fields')
        if password != re_password:
            return render_template('index_2.html', message='Your password and confirmation password do not match')
        if db.session.query(User).filter(User.username == username).count() == 1:
            return render_template('index_2.html', message='This account already exists')
        else:
            data = User(username, password)
            db.session.add(data)
            db.session.commit()
            return render_template('success.html')


if __name__ == '__main__':
    app.run()
