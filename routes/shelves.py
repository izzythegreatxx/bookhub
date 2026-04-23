'''
Shelf-related routes for creating, retrieving, and managing shelves in the user's collection.
Includes routes for creating a new shelf, retrieving all shelves for the authenticated user, 
getting books on a specific shelf, adding a book to a shelf, and removing a book from a shelf. 
Each route ensures that the shelf and book belong to the authenticated user and includes appropriate error
handling for cases such as missing shelves or books, duplicate entries, and invalid input data.
'''

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

import logging

from models import Book, Shelf, ShelfBook, db
from schemas import ShelfSchema, BookSchema



# Blueprint for shelf-related routes and schema initialization for validating shelf data
shelf_schema = ShelfSchema()
book_schema = BookSchema()
shelves_bp = Blueprint("shelves", __name__)

# Helper function to parse JSON payload from the request and ensure it is a valid dictionary
def get_json_payload():
    try:
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return None
        return data
    except Exception as e:
        logging.error(f"Error parsing JSON payload: {e}")
        return None
        

# Route for creating a new shelf for the authenticated user, ensuring the shelf name is unique for that user and validating the input data
@shelves_bp.post("/")
@jwt_required()
def create_shelf():
    try:
        user_id = int(get_jwt_identity())
        # Parse and validate the JSON payload 
        data = get_json_payload()
        if data is None:
            return jsonify({"message": "Request body must be valid JSON"}), 400

        errors = shelf_schema.validate(data)
        if errors:
            return jsonify(errors), 400
        # Ensure the shelf name is provided and not empty after stripping whitespace
        name = data["name"].strip()
        # Check if a shelf with the same name already exists for the user to prevent duplicates
        existing = Shelf.query.filter_by(user_id=user_id, name=name).first()
        if existing:
            return jsonify({"message": "Shelf already exists"}), 409
        # Create a new Shelf object with the provided name and associate it with the authenticated user, then save it to the database
        shelf = Shelf(name=name, user_id=user_id)
        db.session.add(shelf)
        db.session.commit()

        return jsonify({"id": shelf.id, "name": shelf.name}), 201
    except Exception as e:
        logging.error(f"Error creating shelf: {e}")
        return jsonify({"message": "An error occurred while creating the shelf"}), 500

# Route for retrieving all shelves belonging to the authenticated user, returning a list of shelves sorted by name
@shelves_bp.get("/")
@jwt_required()
def get_shelves():
    try:
        user_id = int(get_jwt_identity())
        shelves = Shelf.query.filter_by(user_id=user_id).all()

        return jsonify(
            [
                {
                    "id": shelf.id,
                    "name": shelf.name,
                }
                for shelf in shelves
            ]
        ), 200
    except Exception as e:
        logging.error(f"Error retrieving shelves: {e}")
        return jsonify({"message": "An error occurred while retrieving shelves"}), 500


@shelves_bp.get("/<int:shelf_id>")
@jwt_required()
def get_shelf_books(shelf_id):
    try:
        user_id = int(get_jwt_identity())
        # Retrieve the specified shelf for the authenticated user and return a list of books on that shelf, ensuring the shelf belongs to the user
        shelf = Shelf.query.filter_by(id=shelf_id, user_id=user_id).first()

        if not shelf:
            return jsonify({"error": "Shelf not found"}), 404
        # Get the books associated with the shelf through the ShelfBook association, ensuring only books that belong to the authenticated user are included in the response
        books = [link.book for link in shelf.shelf_books if link.book.user_id == user_id]

        return jsonify(
            [
                {
                    "id": book.id,
                    "title": book.title,
                    "author": book.author,
                    "year": book.year,
                    "status": book.status,
                    "rating": book.rating,
                    "review": book.review,
                    "pages_total": book.pages_total,
                    "pages_read": book.pages_read,
                }
                for book in books
            ]
        ), 200
    except Exception as e:
        logging.error(f"Error retrieving shelf books: {e}")
        return jsonify({"message": "An error occurred while retrieving shelf books"}), 500

# Route for adding a book to a shelf, ensuring both the shelf and book belong to the authenticated user and preventing duplicate entries on the same shelf
@shelves_bp.post("/<int:shelf_id>/books/<int:book_id>")
@jwt_required()
def add_book_to_shelf(shelf_id, book_id):
    try:
        user_id = int(get_jwt_identity())
        # Retrieve the specified shelf for the authenticated user and ensure it exists before attempting to add a book to it
        shelf = Shelf.query.filter_by(id=shelf_id, user_id=user_id).first()
        if not shelf:
            return jsonify({"error": "Shelf not found"}), 404
        # Ensure the book exists and belongs to the authenticated user before attempting to add it to the shelf
        book = Book.query.filter_by(id=book_id, user_id=user_id).first()
        if not book:
            return jsonify({"error": "Book not found"}), 404

        existing = ShelfBook.query.filter_by(shelf_id=shelf_id, book_id=book_id).first()
        if existing:
            return jsonify({"message": "Book already in shelf"}), 409

        shelf_book = ShelfBook(shelf_id=shelf_id, book_id=book_id)
        db.session.add(shelf_book)
        db.session.commit()

        return jsonify({"message": "Book added to shelf"}), 201
    except Exception as e:
        logging.error(f"Error adding book to shelf: {e}")
        return jsonify({"message": "An error occurred while adding the book to the shelf"}), 500

# Route for removing a book from a shelf, ensuring the shelf and book belong to the authenticated user and that the book is currently on the shelf before attempting to remove it
@shelves_bp.delete("/<int:shelf_id>/books/<int:book_id>")
@jwt_required()
def remove_book_from_shelf(shelf_id, book_id):
    try:
        user_id = int(get_jwt_identity())
        # Retrieve the specified shelf and book for the authenticated user to ensure they exist and belong to the user before attempting to remove the book from the shelf
        shelf = Shelf.query.filter_by(id=shelf_id, user_id=user_id).first()
        if not shelf:
            return jsonify({"error": "Shelf not found"}), 404

        book = Book.query.filter_by(id=book_id, user_id=user_id).first()
        if not book:
            return jsonify({"error": "Book not found"}), 404

        shelf_book = ShelfBook.query.filter_by(shelf_id=shelf_id, book_id=book_id).first()
        if not shelf_book:
            return jsonify({"error": "Book not on shelf"}), 404

        db.session.delete(shelf_book)
        db.session.commit()
        return "", 204
    except Exception as e:
        logging.error(f"Error removing book from shelf: {e}")
        return jsonify({"message": "An error occurred while removing the book from the shelf"}), 500

# Delete shelf 
@shelves_bp.delete("/<int:shelf_id>")
@jwt_required()
def delete_shelf(shelf_id):
    try:
        user_id = get_jwt_identity()
        shelf = Shelf.query.filter_by(id=shelf_id, user_id=user_id).first()
        if not shelf:
            return jsonify({"error": "Shelf not found"}), 404
    
        db.session.delete(shelf)
        db.session.commit()
        return jsonify({"message": "Shelf deleted"}), 200
    except Exception as e:
        logging.error(f"Error deleting shelf: {e}")
        return jsonify({"message": "An error occurred while deleting the shelf"}), 500

# Edit shelf name
@shelves_bp.patch("/<int:shelf_id>")
@jwt_required()
def edit_shelf(shelf_id):
    try:
        user_id = get_jwt_identity()
        shelf = Shelf.query.filter_by(id=shelf_id, user_id=user_id).first()
        if not shelf:
            return jsonify({"error": "Shelf not found"}), 404
    
        data = request.get_json()
        new_name = data.get("name", "").strip()
        if not new_name:
            return jsonify({"error": "Shelf name cannot be empty"}), 400
    
        existing = Shelf.query.filter_by(user_id=user_id, name=new_name).first()
        if existing and existing.id != shelf_id:
            return jsonify({"error": "Shelf name already exists"}), 409
    
        shelf.name = new_name
        db.session.commit()
        return jsonify({"message": "Shelf renamed successfully", "shelf": {"id": shelf.id, "name": shelf.name} }), 200
    except Exception as e:
        logging.error(f"Error editing shelf: {e}")
        return jsonify({"message": "An error occurred while editing the shelf"}), 500