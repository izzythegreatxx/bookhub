# BookHub API & Web Application

BookHub is a Flask-based REST API and web application for tracking books, reading progress, custom shelves, ratings, and reviews. Users can manage their personal library with an intuitive, modern interface.

---

## Overview

BookHub allows users to:

- Register an account with a username, email, and password
- Verify their email via a verification link
- Log in with JWT authentication
- Add books to their personal collection
- Update reading status and track progress
- Rate and review books
- Organize books into custom shelves
- Rename or delete shelves using a settings button
- Search, filter, and view books by shelves
- Contact the developer via a web form

This project was built to practice REST API design, full-stack development, and deployment-ready best practices with Flask.

---

## Features

- User registration and login with username, email, and password
- Email verification via Flask-Mail
- JWT authentication with access and refresh tokens
- Password hashing with bcrypt
- CRUD operations for books
- Search, filtering, and pagination for books
- Custom shelves with rename and delete functionality
- Ratings and reviews for books
- Frontend dashboard with dynamic book and shelf management
- Sidebar and topbar button highlighting for improved UX
- Persistent header and descriptive messages per page (Dashboard, Books, Shelves)
- Contact form integrated into the web interface
- Environment variable support with `.env`
- PostgreSQL database with SQLAlchemy ORM (production) and SQLite fallback (development)
- Request validation with Marshmallow
- Logging configuration for monitoring server activity

---

## Tech Stack

- Python
- Flask
- Flask-SQLAlchemy
- Flask-JWT-Extended
- Flask-Mail
- Marshmallow
- PostgreSQL (production), SQLite (development)
- Vanilla JavaScript, HTML, CSS (frontend)

---

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
│   ├── dashboard.html
│   ├── contact.html
│   ├── login.html
│   └── verified.html
└── static/
    ├── styles.css
    └── dashboard.js