from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Shelf, ShelfBook, Book

shelves_bp = Blueprint("shelves", __name__)


@shelves_bp.post("/shelves")
@jwt_required()
def create_shelf():
    user_id = get_jwt_identity()
    data = request.get_json()
    name = data.get("name")

    if not name:
        return jsonify({"message": "Shelf name is required"}), 400

    shelf = Shelf(name=name, user_id=user_id)
    db.session.add(shelf)
    db.session.commit()

    return jsonify({"id": shelf.id, "name": shelf.name}), 201

@shelves_bp.post("/shelves/<int:shelf_id>/books/<int:book_id>")
@jwt_required
def add_book_to_shelf(shelf_id, book_id):
    user_id = get_jwt_identity()

    # ensure shelf belongs to user
    shelf = Shelf.query.filter_by(id=shelf_id, user_id=user_id).first()
    if not shelf:
        return jsonify({"error": "Shelf not found"}), 404

    # ensure book belongs to user
    book = Book.query.filter_by(id=book_id, user_id=user_id).first()
    if not book:
        return jsonify({"error": "Book not found"}), 404

    # prevent duplicates
    existing = ShelfBook.query.filter_by(shelf_id=shelf_id, book_id=book_id).first()
    if existing:
        return jsonify({"message": "Book already in shelf"}), 200

    shelf_book = ShelfBook(shelf_id=shelf_id, book_id=book_id)
    db.session.add(shelf_book)
    db.session.commit()

    return jsonify({"message": "Book added to shelf"}), 201


@shelves_bp.delete("/shelves/<int:shelf_id>/books/<int:book_id>")
@jwt_required()
def remove_book_from_shelf(shelf_id, book_id):
    user_id = get_jwt_identity()

    shelf = Shelf.query.filter_by(id=shelf_id, user_id=user_id).first()
    if not shelf:
        return jsonify({"error": "Shelf not found"}), 404

    shelf_book = ShelfBook.query.filter_by(shelf_id=shelf_id, book_id=book_id).first()
    if not shelf_book:
        return jsonify({"error": "Book not on shelf"}), 404

    db.session.delete(shelf_book)
    db.session.commit()

    return jsonify({"message": "Book removed from shelf"}), 200


@shelves_bp.get("/shelves")
@jwt_required()
def get_shelves():
    user_id = get_jwt_identity()
    shelves = Shelf.query.filter_by(user_id=user_id).all()

    return jsonify([
        {"id": s.id, "name": s.name}
        for s in shelves
    ]), 200

@shelves_bp.get("/shelves/<int:shelf_id>")
@jwt_required()
def get_shelf_books(shelf_id):
    user_id = get_jwt_identity()
    shelf = Shelf.query.filter_by(id=shelf_id, user_id=user_id).first()
    if not shelf:
        return jsonify({"error": "Shelf not found"}), 404

    shelf_books = ShelfBook.query.filter_by(shelf_id=shelf_id).all()
    book_ids = [sb.book_id for sb in shelf_books]

    books = Book.query.filter(Book.id.in_(book_ids)).all()

    return jsonify([
        {
            "id": b.id,
            "title": b.title,
            "author": b.author,
            "year": b.year,
            "status": b.status,
            "rating": b.rating,
            "reveiew": b.review,
            "pages_total": b.pages_total,
            "pages_read": b.pages_read
        }
        for b in books
    ]), 200






