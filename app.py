from flask import Flask, flash, render_template, request, session, redirect, jsonify
from flask import abort
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

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

@app.route('/')
def index():
    return render_template('index.html')

@app.route("/sing_in", methods=['POST'])
def sing_in(): 
    #sing in if you are have account

    # Forget any user_id
    session.clear()

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        #print(username, password)
        if username == '' or password == '':
            return render_template('index.html', message='Please enter required fields')

        result = db.execute('SELECT * FROM users WHERE username=:username and password=:password',
                            {"username": username, "password": password}).fetchone()
        if result == None:
            return render_template('index.html', message ='The email or the password you entered is invalid')

        # Remember which user has logged in
        session["user_id"] = result.id
        session["username"] = result.username
        
        return render_template('search.html')


@app.route("/register")
def register():
    return render_template('index_2.html')

@app.route('/search_page')
def search_page():
    return render_template('search.html')

@app.route("/sing_up", methods=["POST"])
def sing_up():
    # Create an accout
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        re_password = request.form['re_password']
        
        if username == '' or password == '' or re_password == '':
            return render_template('index_2.html', message='Please enter required fields')
        if password != re_password:
            return render_template('index_2.html', message='Your password and confirmation password do not match')
        
        result = db.execute('SELECT * FROM users WHERE username=:username', {"username": username}).fetchone()
        
        if result:
            return render_template('index_2.html', message='The account with this username already exists')
        else:
            # Insert user in db
            db.execute("INSERT INTO users (username, password) VALUES (:username, :password)",
                        {"username": username, "password": password})
            # Commit changes to database
            db.commit()

            # Remember the new user in session
            result = db.execute('SELECT * FROM users WHERE username=:username', {"username": username}).fetchone()

            session["user_id"] = result.id
            session["username"] = result.username

            return render_template('search.html')

@app.route("/result", methods = ["GET"])
def search():
    if request.method == 'GET':
        query_for_book = request.args.get('query_for_book')
        if query_for_book == '':
            return render_template('search.html', message='Please enter isbn, title or author of the book')
        
        #change to use in LIKE sql
        query_for_book = '%'+query_for_book+'%'

        results = db.execute('SELECT * \
                            FROM books \
                            WHERE books.isbn LIKE :query_for_book OR \
                            books.title LIKE :query_for_book OR \
                            books.author LiKE :query_for_book LIMIT 10',
                            {"query_for_book": query_for_book}).fetchall()

        if len(results) == 0: 
            return render_template('search.html', message='There is no match')
        else:
            return render_template('success.html', results=results, my_title = 'Here is what we found on your request')

@app.route("/result/<int:book_id>")
def book(book_id):
    """List details about a single book."""

    # Make sure book exists.
    book = db.execute('Select * FROM books WHERE books.id=:book_id', {"book_id": book_id}).fetchall()
    if book is None:
        return render_template("error.html", message="No such book.")
    #if the book exists
    else:
        #check reviews
        session['book_id'] = book[0][0]
        session['book_isbn'] = book[0][1]
        review = db.execute('SELECT * FROM reviews WHERE reviews.book_isbn=:book_isbn', {"book_isbn":book[0][1]}).fetchall()
        
        #check GOODREADS reviews
        # Read API key from env variable
        key = os.getenv("GOODREADS_KEY")
        
        # Query the api with key and ISBN as parameters
        query = requests.get("https://www.goodreads.com/book/review_counts.json",
                params={"key": key, "isbns": book[0][1]})

        # Convert the response to JSON
        response = query.json()
        response = response['books'][0]
        average_rating = response['average_rating']
        ratings_count = response['ratings_count']

        if len(review) > 0:
            return render_template("book_page.html", book=book[0], comments=review, average_rating=average_rating, ratings_count=ratings_count)
        else:
            return render_template("book_page.html", book=book[0], comments=None, average_rating=average_rating, ratings_count=ratings_count)
     
@app.route('/submit_review', methods=['POST'])
def submit_review():
    if request.method == 'POST':
        try:
            # check if first riview
            result = db.execute('SELECT * FROM reviews WHERE reviews.book_isbn=:book_isbn AND reviews.user_id=:user_id', 
                                {"book_isbn": str(session['book_isbn']), "user_id": session['user_id']}).fetchall()
            if len(result) > 0:
                book_id = str(session['book_id'])
                flash('You already left the review for this book')
                return redirect("/result/" + book_id)
            
            else:
                if request.form['rating'] and request.form['comments']:
                    rating = request.form['rating']
                    comment = request.form['comments']
                    ## Insert review in db
                    db.execute("INSERT INTO reviews (user_id, book_isbn, comment, rating) VALUES (:user_id, :book_isbn, :comment, :rating)",
                                {"user_id": str(session['user_id']), 
                                "book_isbn": str(session['book_isbn']), 
                                "comment": comment, 
                                "rating": rating})
                    # Commit changes to database
                    db.commit()
                    return render_template('success.html', message='Thank you for your review')
        except:
                book_id = str(session['book_id'])
                flash('Provide rating and some comment to the book')
                return redirect("/result/" + book_id) 


@app.route("/api/<isbn>")
def return_json(isbn):

    isbn = str(isbn)
    result = db.execute('SELECT title, author, year, isbn, \
                        COUNT(reviews.id) as review_count, \
                        AVG(CAST(reviews.rating AS int)) as average_score \
                        FROM books \
                        LEFT JOIN reviews \
                        ON books.isbn = reviews.book_isbn \
                        WHERE isbn = :isbn \
                        GROUP BY title, author, year, isbn', 
                        {'isbn': isbn})
    
    if result.rowcount < 1:
        #return jsonify({"Error": "Invalid book ISBN"}), 422
        abort(404)

    # Fetch result from RowProxy    
    tmp = result.fetchone()
    result = dict(tmp.items())
    if result['average_score']:
        result['average_score'] = float('%.2f'%(result['average_score']))

    return jsonify({'result': result})


if __name__ == '__main__':
    app.run()
