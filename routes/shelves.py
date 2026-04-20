from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from models import Book, Shelf, ShelfBook, db
from schemas import ShelfSchema

shelf_schema = ShelfSchema()
shelves_bp = Blueprint("shelves", __name__)


def get_json_payload():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None
    return data


@shelves_bp.post("/shelves")
@jwt_required()
def create_shelf():
    user_id = int(get_jwt_identity())
    data = get_json_payload()
    if data is None:
        return jsonify({"message": "Request body must be valid JSON"}), 400

    errors = shelf_schema.validate(data)
    if errors:
        return jsonify(errors), 400

    name = data["name"].strip()

    existing = Shelf.query.filter_by(user_id=user_id, name=name).first()
    if existing:
        return jsonify({"message": "Shelf already exists"}), 409

    shelf = Shelf(name=name, user_id=user_id)
    db.session.add(shelf)
    db.session.commit()

    return jsonify({"id": shelf.id, "name": shelf.name}), 201


@shelves_bp.get("/shelves")
@jwt_required()
def get_shelves():
    user_id = int(get_jwt_identity())
    shelves = Shelf.query.filter_by(user_id=user_id).order_by(Shelf.name.asc()).all()

    return jsonify(
        [{"id": shelf.id, "name": shelf.name} for shelf in shelves]
    ), 200


@shelves_bp.get("/shelves/<int:shelf_id>")
@jwt_required()
def get_shelf_books(shelf_id):
    user_id = int(get_jwt_identity())
    shelf = Shelf.query.filter_by(id=shelf_id, user_id=user_id).first()

    if not shelf:
        return jsonify({"error": "Shelf not found"}), 404

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


@shelves_bp.post("/shelves/<int:shelf_id>/books/<int:book_id>")
@jwt_required()
def add_book_to_shelf(shelf_id, book_id):
    user_id = int(get_jwt_identity())

    shelf = Shelf.query.filter_by(id=shelf_id, user_id=user_id).first()
    if not shelf:
        return jsonify({"error": "Shelf not found"}), 404

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


@shelves_bp.delete("/shelves/<int:shelf_id>/books/<int:book_id>")
@jwt_required()
def remove_book_from_shelf(shelf_id, book_id):
    user_id = int(get_jwt_identity())

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