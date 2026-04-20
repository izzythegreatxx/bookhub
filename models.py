from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint, UniqueConstraint
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()


book_tags = db.Table(
    "book_tags",
    db.Column("book_id", db.Integer, db.ForeignKey("book.id"), primary_key=True),
    db.Column("tag_id", db.Integer, db.ForeignKey("tag.id"), primary_key=True),
)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)

    books = db.relationship("Book", back_populates="user", cascade="all, delete-orphan")
    shelves = db.relationship("Shelf", back_populates="user", cascade="all, delete-orphan")
    tags = db.relationship("Tag", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class Book(db.Model):
    __table_args__ = (
        CheckConstraint("rating IS NULL OR (rating >= 1 AND rating <= 5)", name="check_rating_range"),
        CheckConstraint("pages_read >= 0", name="check_pages_read_nonnegative"),
        CheckConstraint("pages_total IS NULL OR pages_total >= 1", name="check_pages_total_positive"),
        CheckConstraint(
            "pages_total IS NULL OR pages_read <= pages_total",
            name="check_pages_read_lte_pages_total",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False, index=True)
    author = db.Column(db.String(100), nullable=False, index=True)
    year = db.Column(db.Integer, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    user = db.relationship("User", back_populates="books")

    status = db.Column(db.String(50), default="want_to_read", nullable=False)
    rating = db.Column(db.Integer, nullable=True)
    review = db.Column(db.Text, nullable=True)
    pages_total = db.Column(db.Integer, nullable=True)
    pages_read = db.Column(db.Integer, default=0, nullable=False)

    tags = db.relationship("Tag", secondary=book_tags, back_populates="books")
    shelf_links = db.relationship("ShelfBook", back_populates="book", cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "author": self.author,
            "year": self.year,
            "status": self.status,
            "rating": self.rating,
            "review": self.review,
            "pages_total": self.pages_total,
            "pages_read": self.pages_read,
            "user_id": self.user_id,
            "tags": [tag.name for tag in self.tags],
            "shelves": [link.shelf.name for link in self.shelf_links],
        }


class Tag(db.Model):
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_tag_user_name"),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)

    user = db.relationship("User", back_populates="tags")
    books = db.relationship("Book", secondary=book_tags, back_populates="tags")


class Shelf(db.Model):
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_shelf_user_name"),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)

    user = db.relationship("User", back_populates="shelves")
    shelf_books = db.relationship("ShelfBook", back_populates="shelf", cascade="all, delete-orphan")


class ShelfBook(db.Model):
    __table_args__ = (
        UniqueConstraint("shelf_id", "book_id", name="uq_shelf_book"),
    )

    id = db.Column(db.Integer, primary_key=True)
    shelf_id = db.Column(db.Integer, db.ForeignKey("shelf.id"), nullable=False, index=True)
    book_id = db.Column(db.Integer, db.ForeignKey("book.id"), nullable=False, index=True)

    shelf = db.relationship("Shelf", back_populates="shelf_books")
    book = db.relationship("Book", back_populates="shelf_links")