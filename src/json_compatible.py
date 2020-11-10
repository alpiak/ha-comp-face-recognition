"""Class of objects that can be converted to JSON."""

class JSONCompatible():
    """Objects that can be converted to JSON."""

    @classmethod
    def from_json(cls, json_object):
        """Create the entry from json object."""
        raise NotImplementedError()

    def to_json(self):
        """Convert the entry to json object."""
        raise NotImplementedError()
