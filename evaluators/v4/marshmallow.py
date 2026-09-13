"""Behavioral regression from Marshmallow #2170 / PR #2792; MIT license.

Copyright Steven Loria and contributors. See licenses/marshmallow.txt.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(sys.argv[1]).resolve() / "src"))
from marshmallow import Schema, fields, validates, validates_schema, ValidationError


class Aliased(Schema):
    value = fields.Int(data_key="externalValue")

    @validates("value")
    def validate_value(self, value, **kwargs):
        raise ValidationError("field error")

    @validates_schema(skip_on_field_errors=False)
    def validate_schema(self, data, **kwargs):
        raise ValidationError("schema error", field_name="value")

    @validates_schema(skip_on_field_errors=False)
    def validate_dictionary(self, data, **kwargs):
        raise ValidationError({"externalValue": ["literal error"]})


def messages(schema, data):
    try:
        schema.load(data)
    except ValidationError as error:
        return error.messages
    raise AssertionError("validation errors must remain visible")


for many in [False, True]:
    data = [{"externalValue": 4}] if many else {"externalValue": 4}
    actual = messages(Aliased(many=many), data)
    if many:
        assert set(actual) == {0}, f"many=True must retain indexed errors: {actual}"
        actual = actual[0]
    assert set(actual) == {"externalValue"}, f"field and schema errors must share the external key: {actual}"
    assert sorted(actual["externalValue"]) == ["field error", "literal error", "schema error"]

for declared, error_field, expected_key in [
    ("value", "value", "externalValue"),
    ("value", "_schema", "_schema"),
    ("value", "unknown", "unknown"),
]:
    class Selected(Schema):
        value = fields.Int(data_key="externalValue")

        @validates_schema
        def check(self, data, **kwargs):
            raise ValidationError("invalid", field_name=error_field)

    for schema in [Selected(), Selected(exclude=(declared,))]:
        assert messages(schema, {}) == {expected_key: ["invalid"]}, "declared/excluded aliases, schema errors and unknown names must retain their semantics"
print("PASS: alias merging, many indexing, excluded declared fields, schema errors, literal dictionaries")
