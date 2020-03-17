from flask import Flask, flash, render_template, request, session, redirect, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from models import *
from sqlalchemy import or_

#for API
import requests
import json


app = Flask(__name__)

# set up environment
ENV = 'dev'
if ENV == 'dev':
    app.debug = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:123456@127.0.0.3/book_user'
else:
    app.debug = False
    app.config['SQLALCHEMY_DATABASE_URI'] = ''

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

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

    # Forget any user_id
    session.clear()

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        #print(username, password)
        if username == '' or password == '':
            return render_template('index.html', message='Please enter required fields')
        if db.session.query(User).filter(User.username == username, User.password == password).count() == 0:
            return render_template('index.html', message ='The email or password you entered is invalid')
        
        result = db.session.query(User).filter(User.username == username, User.password == password).first()
        
        # Remember which user has logged in
        session["user_id"] = result.id
        session["username"] = result.username
        
        return render_template('search.html')


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

@app.route("/result", methods = ["GET"])
def search():
    if request.method == 'GET':
        isbn = request.args.get('isbn')
        title = request.args.get('title')
        author = request.args.get('author')
        if isbn == '' and title == '' and author == '':
            return render_template('search.html', message='Please enter al least one field')
        if db.session.query(Book).filter(or_(Book.isbn == isbn, Book.title == title, Book.author == author)).count() == 0:
            return render_template('search.html', message='There is no match')
        else:
            results = db.session.query(Book).filter(or_(Book.isbn == isbn, Book.title == title, Book.author == author))
            return render_template('success.html', results=results)

@app.route("/result/<int:book_id>")
def book(book_id):
    """List details about a single book."""

    # Make sure book exists.
    book = db.session.query(Book).filter(Book.id == book_id).first()
    if book is None:
        return render_template("error.html", message="No such book.")
    #if the book exists
    else:
        #check reviews
        session['book_id'] = book_id
        session['book_isbn'] = book.isbn
        num_review = db.session.query(Review).filter(Review.book_isbn == book.isbn).count()

        #check GOODREADS reviews
        # Read API key from env variable
        key = os.getenv("GOODREADS_KEY")
        
        # Query the api with key and ISBN as parameters
        query = requests.get("https://www.goodreads.com/book/review_counts.json",
                params={"key": key, "isbns": book.isbn})

        # Convert the response to JSON
        response = query.json()
        response = response['books'][0]
        average_rating = response['average_rating']
        ratings_count = response['ratings_count']

        # add var to the session
        #session['average_rating'] = average_rating
        #session['ratings_count'] = ratings_count
        #session['book'] = book

        if num_review > 0:
            review = db.session.query(Review).filter(Review.book_isbn == book.isbn)
            #session['review'] = review
            return render_template("book_page.html", book=book, comments=review, average_rating=average_rating, ratings_count=ratings_count)
        else:
            return render_template("book_page.html", book=book, comments=None, average_rating=average_rating, ratings_count=ratings_count)
        
@app.route('/submit_review', methods=['POST'])
def submit_review():
    if request.method == 'POST':
        try:
            if request.form['rating'] and request.form['comments']:
                rating = request.form['rating']
                comment = request.form['comments']
                # add to db
                review = Review(user_id=session["user_id"], book_isbn=session["book_isbn"], comment=comment, rating=rating)
                db.session.add(review)
                db.session.commit()
                return render_template('success.html')
        except:
            book_id = str(session['book_id'])
            flash('Provide rating and some comment to the book')
            return redirect("/result/" + book_id) #, message='Provide rating and some comment to the book')

@app.route("/api/<int:isbn>")
def return_json(isbn):

    result = db.execute("SELECT title, author, year, isbn, \
                    COUNT(reviews.id) as review_count, \
                    AVG(reviews.rating) as average_score \
                    FROM books \
                    INNER JOIN reviews \
                    ON books.id = reviews.book_id \
                    WHERE isbn = :isbn \
                    GROUP BY title, author, year, isbn",
                    {"isbn": isbn})

    return jsonify(result)

if __name__ == '__main__':
    app.run()
