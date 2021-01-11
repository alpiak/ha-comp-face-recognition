"""Class of objects that can be converted to JSON."""

class JSONable():
    """Objects that can be converted to JSON."""

    def __init__(self, entry_type: str):
        self._type = entry_type

    @classmethod
    def from_json(cls, json_object):
        """Create the entry from json object."""
        raise NotImplementedError()

    def to_json(self):
        """Convert the entry to json object."""
        raise NotImplementedError()
