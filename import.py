import os, csv

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from flask_sqlalchemy import SQLAlchemy

# database engine object from SQLAlchemy that manages connections to the database
engine = create_engine(os.getenv("DATABASE_URL"))

# create a 'scoped session' that ensures different users' interactions with the
# database are kept separate
db = scoped_session(sessionmaker(bind=engine))

with open("books.csv", mode='r') as file:
    reader = csv.reader(file, delimiter=',')
    next(reader)
    for isbn, title, author, year in reader:
        print(isbn, title, author, year)
        db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)",
                {"isbn": isbn, 
                 "title": title,
                 "author": author,
                 "year": year})

        print(f"Added book {title} to database.")
    db.commit()   

if __name__ == "__main__":
    main()