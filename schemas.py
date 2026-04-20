from marshmallow import Schema, ValidationError, fields, validate, validates_schema


BOOK_STATUSES = ("want_to_read", "currently_reading", "read")


class BookSchema(Schema):
    id = fields.Int(dump_only=True)
    title = fields.Str(required=True, validate=validate.Length(min=1))
    author = fields.Str(required=True, validate=validate.Length(min=1))
    year = fields.Int(required=True, validate=validate.Range(min=1))

    status = fields.Str(validate=validate.OneOf(BOOK_STATUSES))
    rating = fields.Int(validate=validate.Range(min=1, max=5))
    review = fields.Str()
    pages_total = fields.Int(validate=validate.Range(min=1))
    pages_read = fields.Int(validate=validate.Range(min=0))

    @validates_schema
    def validate_page_progress(self, data, **kwargs):
        pages_total = data.get("pages_total")
        pages_read = data.get("pages_read")

        if pages_total is not None and pages_read is not None and pages_read > pages_total:
            raise ValidationError(
                {"pages_read": ["Pages read cannot exceed pages total"]}
            )


class ShelfSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=1))

