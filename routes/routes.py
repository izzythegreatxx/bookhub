'''
Book-related routes for adding, retrieving, and searching books in the user's collection.
Includes helper functions for JSON payload handling and book data validation, as well as routes for updating and deleting books. 
All routes require JWT authentication to ensure that users can only access and modify their own book data.
'''

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Book
from schemas import BookSchema, BOOK_STATUSES
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_


books_bp = Blueprint("books", __name__)
book_schema = BookSchema()
books_schema = BookSchema(many=True)

# GET all books for current user
@books_bp.route("/", methods=["GET"])
@jwt_required()
def get_books():
    user_id = get_jwt_identity()
    books = Book.query.filter_by(user_id=user_id).all()
    return jsonify(books_schema.dump(books)), 200

# GET single book
@books_bp.route("/<int:book_id>", methods=["GET"])
@jwt_required()
def get_book(book_id):
    user_id = get_jwt_identity()
    book = Book.query.filter_by(id=book_id, user_id=user_id).first()
    if not book:
        return jsonify({"message": "Book not found"}), 404
    return jsonify(book_schema.dump(book)), 200

# POST create new book
@books_bp.route("/", methods=["POST"])
@jwt_required()
def create_book():
    user_id = get_jwt_identity()
    data = request.get_json()
    if not data:
        return jsonify({"message": "No data provided"}), 400

    book = Book(user_id=user_id, **data)
    db.session.add(book)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "Book with this title already exists"}), 409

    return jsonify(book_schema.dump(book)), 200

# Update book details, allowing partial updates and ensuring that the updated title does not conflict with existing books in the user's collection
@books_bp.route("/<int:book_id>", methods=["PATCH"])
@jwt_required()
def update_book(book_id):
    user_id = get_jwt_identity()
    book = Book.query.filter_by(id=book_id, user_id=user_id).first()
    if not book:
        return jsonify({"message": "Book not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"message": "No data provided"}), 400

    # Check if another book with the same title exists
    if "title" in data:
        existing = Book.query.filter(
            and_(Book.user_id == user_id, Book.title == data["title"], Book.id != book_id)
        ).first()
        if existing:
            return jsonify({"message": "Book title already exists"}), 409

    # Update fields
    for field in ["title", "author", "year", "status", "pages_total", "pages_read", "rating", "review"]:
        if field in data:
            setattr(book, field, data[field])
            
    # Logical validation
    errors = []

    # Non-negative pages
    if book.pages_total is not None and book.pages_total < 0:
        errors.append("Total pages cannot be negative.")

    if book.pages_read is not None and book.pages_read < 0:
        errors.append("Pages read cannot be negative.")

    # Pages read cannot exceed total
    if book.pages_total is not None and book.pages_read is not None:
        if book.pages_read > book.pages_total:
            errors.append("Pages read cannot exceed total pages.")

    # Rating validation
    if book.rating is not None and (book.rating < 1 or book.rating > 5):
        errors.append("Rating must be between 1 and 5.")

    if errors:
        return jsonify({"message": "Validation failed", "errors": errors}), 400
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 400

    return jsonify(book_schema.dump(book)), 200

# DELETE book
@books_bp.route("/<int:book_id>", methods=["DELETE"])
@jwt_required()
def delete_book(book_id):
    user_id = get_jwt_identity()
    book = Book.query.filter_by(id=book_id, user_id=user_id).first()
    if not book:
        return jsonify({"message": "Book not found"}), 404

    db.session.delete(book)
    db.session.commit()
    return jsonify({"message": "Book deleted"}), 200

# Route for searching books in the user's collection based on various criteria and supporting pagination and sorting
@books_bp.get("/books/search")
@jwt_required()
def search_books():
    user_id = int(get_jwt_identity())

    author = request.args.get("author")
    title = request.args.get("title")
    year = request.args.get("year", type=int)
    status = request.args.get("status")
    
    # Sorting parameters with default values and validation to ensure only allowed fields are used for sorting
    sort_by = request.args.get("sort_by", "id")
    order = request.args.get("order", "desc")
    
    # Pagination parameters with default values and limits to prevent excessive data retrieval
    page = max(request.args.get("page", 1, type=int), 1)
    limit = min(max(request.args.get("limit", 10, type=int), 1), 100)

    query = Book.query.filter_by(user_id=user_id)

    if author:
        query = query.filter(Book.author.ilike(f"%{author}%"))
    if title:
        query = query.filter(Book.title.ilike(f"%{title}%"))
    if year is not None:
        query = query.filter(Book.year == year)
    if status in BOOK_STATUSES:
        query = query.filter(Book.status == status)
        
    # Validate sorting parameters and apply sorting to the query based on allowed fields
    allowed_sort_fields = {"id", "title", "author", "year", "rating", "status", "pages_read"}
    if sort_by in allowed_sort_fields:
        column = getattr(Book, sort_by)
        if order == "asc":
            query = query.order_by(column.asc())
        else:
            query = query.order_by(column.desc())

    results = query.paginate(page=page, per_page=limit, error_out=False)

    return jsonify(
        {
            "total": results.total,
            "page": page,
            "limit": limit,
            "results": books_schema.dump(results.items),
        }
    ), 200


