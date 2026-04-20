from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from models import Book, db
from schemas import BOOK_STATUSES, BookSchema

book_schema = BookSchema()
books_schema = BookSchema(many=True)
books_bp = Blueprint("books", __name__)


def get_json_payload():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None
    return data


def validate_book_payload(data, partial=False):
    errors = book_schema.validate(data, partial=partial)
    if errors:
        return errors

    status = data.get("status")
    if status is not None and status not in BOOK_STATUSES:
        return {"status": [f"Status must be one of: {', '.join(BOOK_STATUSES)}"]}

    return {}


@books_bp.post("/books")
@jwt_required()
def add_book():
    data = get_json_payload()
    if data is None:
        return jsonify({"message": "Request body must be valid JSON"}), 400

    errors = validate_book_payload(data, partial=False)
    if errors:
        return jsonify(errors), 400

    user_id = int(get_jwt_identity())

    new_book = Book(
        title=data["title"].strip(),
        author=data["author"].strip(),
        year=data["year"],
        user_id=user_id,
        status=data.get("status", "want_to_read"),
        rating=data.get("rating"),
        review=data.get("review"),
        pages_total=data.get("pages_total"),
        pages_read=data.get("pages_read", 0),
    )

    db.session.add(new_book)
    db.session.commit()

    return jsonify(book_schema.dump(new_book)), 201


@books_bp.get("/books")
@jwt_required()
def get_books():
    user_id = int(get_jwt_identity())
    books = Book.query.filter_by(user_id=user_id).order_by(Book.id.desc()).all()
    return jsonify(books_schema.dump(books)), 200


@books_bp.get("/books/<int:book_id>")
@jwt_required()
def get_book(book_id):
    user_id = int(get_jwt_identity())
    book = Book.query.filter_by(id=book_id, user_id=user_id).first()

    if not book:
        return jsonify({"message": "Book not found"}), 404

    return jsonify(book_schema.dump(book)), 200


@books_bp.get("/books/search")
@jwt_required()
def search_books():
    user_id = int(get_jwt_identity())

    author = request.args.get("author")
    title = request.args.get("title")
    year = request.args.get("year", type=int)
    status = request.args.get("status")

    sort_by = request.args.get("sort_by", "id")
    order = request.args.get("order", "desc")

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


@books_bp.patch("/books/<int:book_id>")
@jwt_required()
def update_book(book_id):
    user_id = int(get_jwt_identity())
    book = Book.query.filter_by(id=book_id, user_id=user_id).first()

    if not book:
        return jsonify({"message": "Book not found"}), 404

    data = get_json_payload()
    if data is None:
        return jsonify({"message": "Request body must be valid JSON"}), 400

    errors = validate_book_payload(data, partial=True)
    if errors:
        return jsonify(errors), 400

    if "title" in data:
        book.title = data["title"].strip()
    if "author" in data:
        book.author = data["author"].strip()
    if "year" in data:
        book.year = data["year"]
    if "status" in data:
        book.status = data["status"]
    if "rating" in data:
        book.rating = data["rating"]
    if "review" in data:
        book.review = data["review"]
    if "pages_total" in data:
        book.pages_total = data["pages_total"]
    if "pages_read" in data:
        book.pages_read = data["pages_read"]

    if book.pages_total is not None and book.pages_read > book.pages_total:
        return jsonify({"pages_read": ["Pages read cannot exceed pages total"]}), 400

    db.session.commit()
    return jsonify(book_schema.dump(book)), 200


@books_bp.delete("/books/<int:book_id>")
@jwt_required()
def delete_book(book_id):
    user_id = int(get_jwt_identity())
    book = Book.query.filter_by(id=book_id, user_id=user_id).first()

    if not book:
        return jsonify({"message": "Book not found"}), 404

    db.session.delete(book)
    db.session.commit()
    return "", 204