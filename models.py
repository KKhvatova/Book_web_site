import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):

    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=False, unique=True, nullable=False)
    password = db.Column(db.String(80), index=True, nullable=False)
    
    def __init__(self, username, password):
        self.username = username
        self.password = password

class Book(db.Model):

    __tablename__ = 'books'
    id = db.Column(db.Integer, primary_key=True)
    isbn = db.Column(db.String(80), index=False, nullable=False)
    title = db.Column(db.String(80), index=False, nullable=False)
    author = db.Column(db.String(80), index=False, nullable=False)
    year = db.Column(db.Integer, index=False, nullable=False)
    
    def __init__(self, isbn, title, author, year):
        self.isbn = isbn
        self.title = title
        self.author = author
        self.year = year
        