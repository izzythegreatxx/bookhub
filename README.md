# BookHub API & Web Application

BookHub is a Flask-based REST API and web application for tracking books, reading progress, custom shelves, ratings, and reviews. It allows users to manage their personal library with an intuitive and modern interface.

## Overview

BookHub allows users to:

- Register an account and verify their email
- Log in with JWT authentication
- Add books to their personal collection
- Update reading status and track progress
- Rate and review books
- Organize books into custom shelves
- Edit and delete shelves
- Search, filter, and view books by shelves

This project was built to practice REST API design and full-stack development with Flask.

## Features

- User registration and login with username, email, and password
- Email verification via Flask-Mail
- JWT authentication with access and refresh tokens
- CRUD operations for books
- Search, filtering, and pagination for books
- Custom shelves with rename and delete functionality
- Ratings and reviews for books
- Frontend dashboard with dynamic book and shelf management
- Settings button on shelves for quick actions (rename/delete)
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
- Vanilla JavaScript, HTML, CSS (for frontend)

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