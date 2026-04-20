# BookHub API

A Flask REST API for tracking books, reading progress, shelves, ratings, and reviews.

## Overview

BookHub API allows users to:

- register an account
- verify their email
- log in with JWT authentication
- add books to their personal collection
- update reading status and progress
- rate and review books
- organize books into custom shelves
- search and filter books

This project was built to practice REST API design with Flask.

## Features

- User registration and login
- Email verification
- JWT authentication with access and refresh tokens
- CRUD operations for books
- Search, filtering, sorting, and pagination for books
- Custom shelves for organizing books
- Ratings and reviews
- Environment variable support with `.env`
- SQLite database with SQLAlchemy ORM
- Request validation with Marshmallow

## Tech Stack

- Python
- Flask
- Flask-SQLAlchemy
- Flask-JWT-Extended
- Flask-Mail
- Marshmallow
- SQLite

## Project Structure

```text
.
├── main.py
├── models.py
├── schemas.py
├── blocklist.py
├── mail_config.py
├── requirements.txt
├── README.md
├── .env
├── instance/
├── routes/
│   ├── auth.py
│   ├── routes.py
│   └── shelves.py
├── templates/
└── static/