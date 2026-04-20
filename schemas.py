'''
Schemas for validating and serializing Book and Shelf data using Marshmallow, including custom validation to ensure data integrity.
The BookSchema defines fields for book attributes such as title, author, year, status, rating, review, and page counts, along with 
validation rules for each field. The ShelfSchema defines fields for shelf attributes such as name and includes validation to ensure the name is provided and not empty.
'''

from marshmallow import Schema, ValidationError, fields, validate, validates_schema

# Define allowed book statuses for validation
BOOK_STATUSES = ("want_to_read", "currently_reading", "read")

# Schema for validating and serializing Book data, including custom validation to ensure pages_read does not exceed pages_total
class BookSchema(Schema):
    id = fields.Int(dump_only=True)
    title = fields.Str(required=True, validate=validate.Length(min=1))
    author = fields.Str(required=True, validate=validate.Length(min=1))
    year = fields.Int(required=True, validate=validate.Range(min=1))
    # Status must be one of the predefined BOOK_STATUSES
    status = fields.Str(validate=validate.OneOf(BOOK_STATUSES))
    # Rating must be an integer between 1 and 5 if provided
    rating = fields.Int(validate=validate.Range(min=1, max=5))
    # Review is an optional string field for user reviews of the book
    review = fields.Str()
    pages_total = fields.Int(validate=validate.Range(min=1))
    pages_read = fields.Int(validate=validate.Range(min=0))
    # Custom validation to ensure pages_read does not exceed pages_total when both fields are provided
    @validates_schema
    def validate_page_progress(self, data, **kwargs):
        pages_total = data.get("pages_total")
        pages_read = data.get("pages_read")

        if pages_total is not None and pages_read is not None and pages_read > pages_total:
            raise ValidationError(
                {"pages_read": ["Pages read cannot exceed pages total"]}
            )

# Schema for validating and serializing Shelf data, ensuring the name field is required and not empty
class ShelfSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=1))

