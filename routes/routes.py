from flask import Blueprint, request, jsonify
from models import db, Book
from schemas import BookSchema
from flask_jwt_extended import jwt_required, get_jwt_identity

book_schema = BookSchema()
books_bp = Blueprint("books", __name__)

# Add new book
@books_bp.post("/books")
@jwt_required()
def add_book():
    data = request.get_json()
    errors = book_schema.validate(data)
    if errors:
        return jsonify(errors), 400

    user_id = get_jwt_identity()

    new_book = Book(
        title = data["title"],
        author = data["author"],
        year = data["year"],
        user_id = user_id,
        status=data.get("status", "want_to_read"),
        rating=data.get("rating"),
        review=data.get("review"),
        pages_total=data.get("pages_total"),
        pages_read=data.get("pages_read", 0)
    )
    db.session.add(new_book)
    db.session.commit()

    return jsonify(book_schema.dump(new_book)), 201


# Get all books
@books_bp.get("/books")
@jwt_required()
def get_books():
    user_id = get_jwt_identity()
    books = Book.query.filter_by(user_id=user_id).all()
    return jsonify(book_schema.dump(books, many=True)), 200


# Get one book
@books_bp.get("/books/<int:book_id>")
@jwt_required()
def get_book(book_id):
    user_id = get_jwt_identity()
    book = Book.query.filter_by(user_id=user_id).first()
    if not book:
        return jsonify({"message": "book not found"}), 404
    return jsonify(book_schema.dump(book)), 200


# Search books
@books_bp.get("/books/search")
@jwt_required()
def search_books():
    user_id = get_jwt_identity()
    author = request.args.get("author")
    title = request.args.get("title")
    year = request.args.get("year", type=int)

    sort_by = request.args.get("sort_by")
    order = request.args.get("order", "asc")

    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 10, type=int)

    query = Book.query.filter_by(user_id=user_id)

    # Partial matches
    if author:
        query = query.filter(Book.author.ilike(f"%{author}%"))
    if title:
        query = query.filter(Book.title.ilike(f"%{title}%"))
    if year:
        query = query.filter(Book.year == year)

    # Sorting
    if sort_by in ("title", "author", "year"):
        column = getattr(Book, sort_by)
        if order == "desc":
            column = column.desc()
        query = query.order_by(column)

    # Pagination
    results = query.paginate(page=page, per_page=limit, error_out=False)

    return jsonify({
        "total": results.total,
        "page": page,
        "limit": limit,
        "results": book_schema.dump(results.items, many=True)
    }), 200


# Update book
@books_bp.put("/books/<int:book_id>")
@jwt_required()
def update_book(book_id):
    user_id = get_jwt_identity()
    book = Book.query.filter_by(id = book_id, user_id=user_id).first()

    if not book:
        return jsonify({"message": "book not found"}), 404

    data = request.get_json()
    errors = book_schema.validate(data, partial=True)
    if errors:
        return jsonify(errors), 400

    book.title = data.get("title", book.title)
    book.author = data.get("author", book.author)
    book.year = data.get("year", book.year)

    book.status = data.get("status", book.status)
    book.rating = data.get("rating", book.rating)
    book.review = data.get("review", book.review)
    book.pages_total = data.get("pages_total", book.pages_total)
    book.pages_read = data.get("pages_read", book.pages_read)

    db.session.commit()
    return jsonify(book_schema.dump(book)), 200


# Delete book
@books_bp.delete("/books/<int:book_id>")
@jwt_required()
def delete_book(book_id):
    user_id = get_jwt_identity()
    book = Book.query.filter_by(id = book_id, user_id=user_id).first()
    if not book:
        return jsonify({"message": "book not found"}), 404

    db.session.delete(book)
    db.session.commit()
    return jsonify({"message": "book deleted"}), 200
