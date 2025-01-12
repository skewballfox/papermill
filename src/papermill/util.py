from datetime import datetime
from json import JSONEncoder
from pathlib import Path
from fancy_dataclass import JSONSerializable
from traitlets import Any


class JSONPathSerializable(JSONSerializable):
    """Mixin class enabling conversion of an object to/from JSON."""

    def json_encoder(cls):
        """Override this method to create a custom `JSONEncoder` to handle specific data types.
        A skeleton for this looks like:

        ```
        class Encoder(JSONEncoder):
            def default(self, obj):
                return json.JSONEncoder.default(self, obj)
        ```
        """

        class Encoder(JSONEncoder):
            def default(self, obj: Any) -> Any:
                if isinstance(obj, datetime):
                    return obj.isoformat()  # type: ignore
                if isinstance(obj, Path):
                    return str(obj)
                return JSONEncoder.default(self, obj)

        return Encoder
