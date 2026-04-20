from marshmallow import Schema, fields, validate, ValidationError

class BookSchema(Schema):
    id = fields.Int(dump_only=True)
    title = fields.Str(required=True, validate=validate.Length(min=1))
    author = fields.Str(required=True, validate=validate.Length(min=1))
    year = fields.Int(required=True, validate=validate.Range(min=1))

    status = fields.Str(validate=validate.OneOf(["want_to_read", "reading", "read"]))
    rating = fields.Int(validate=validate.Range(min=1, max=5))
    review = fields.Str()
    pages_total = fields.Int(validate=validate.Range(min=1))
    pages_read = fields.Int(validate=validate.Range(min=0))

