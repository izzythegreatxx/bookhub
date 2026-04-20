'''
Book-related routes for adding, retrieving, and searching books in the user's collection.
Includes helper functions for JSON payload handling and book data validation, as well as routes for updating and deleting books. 
All routes require JWT authentication to ensure that users can only access and modify their own book data.
'''

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from models import Book, db
from schemas import BOOK_STATUSES, BookSchema

# Blueprint for book-related routes
book_schema = BookSchema()
books_schema = BookSchema(many=True)
books_bp = Blueprint("books", __name__)

# Helper functions for JSON payload handling and book data validation
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

# Route for adding a new book to the user's collection
@books_bp.post("/books")
@jwt_required()
def add_book():
    data = get_json_payload()
    if data is None:
        return jsonify({"message": "Request body must be valid JSON"}), 400
    
    # Validate the book data and return errors if validation fails
    errors = validate_book_payload(data, partial=False)
    if errors:
        return jsonify(errors), 400
    # Get the user ID from the JWT token to associate the new book with the correct user
    user_id = int(get_jwt_identity())

    # Create a new Book object with the provided data and associate it with the user
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
    
    # Add the new book to the database session and commit it to save the book in the database
    db.session.add(new_book)
    db.session.commit()

    return jsonify(book_schema.dump(new_book)), 201

# Route for retrieving all books in the user's collection, ordered by most recently added
@books_bp.get("/books")
@jwt_required()
def get_books():
    user_id = int(get_jwt_identity())
    books = Book.query.filter_by(user_id=user_id).order_by(Book.id.desc()).all()
    return jsonify(books_schema.dump(books)), 200

# Route for retrieving a specific book by its ID, ensuring it belongs to the authenticated user
@books_bp.get("/books/<int:book_id>")
@jwt_required()
def get_book(book_id):
    user_id = int(get_jwt_identity())
    book = Book.query.filter_by(id=book_id, user_id=user_id).first()

    if not book:
        return jsonify({"message": "Book not found"}), 404

    return jsonify(book_schema.dump(book)), 200

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

# Route for updating an existing book's information, ensuring the book belongs to the authenticated user and validating the input data
@books_bp.patch("/books/<int:book_id>")
@jwt_required()
def update_book(book_id):
    user_id = int(get_jwt_identity())
    # Retrieve the book to be updated, ensuring it belongs to the authenticated user
    book = Book.query.filter_by(id=book_id, user_id=user_id).first()

    if not book:
        return jsonify({"message": "Book not found"}), 404

    data = get_json_payload()
    if data is None:
        return jsonify({"message": "Request body must be valid JSON"}), 400
    
    # Validate the updated book data and return errors if validation fails (partial=True allows for partial updates)
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

# Route for deleting a book from the user's collection, ensuring the book belongs to the authenticated user before deletion
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