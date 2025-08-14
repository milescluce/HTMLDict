from pathlib import Path

import pandas as pd
from loguru import logger as log
from jinja2 import Environment, FileSystemLoader

CWD = Path(__file__).parent
TEMPLATES = CWD / "templates"
TEMPLATER = Environment(loader=FileSystemLoader(TEMPLATES))

class HTMLDict(dict):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Check annotations for reserved names
        annotations = getattr(self.__class__, '__annotations__', {})
        for anno in annotations:
            if anno in ["card", "detail", "label", "export", "from_pandas_row"]:
                raise AttributeError(f"You cannot use annotations in this dataclass called '{anno}'")

        log.debug(f"Initialized HTMLDict with keys: {list(self.keys())}")

    def __getattribute__(self, item):
        # Avoid infinite recursion by using object.__getattribute__ for class attributes
        try:
            annotations = object.__getattribute__(self, '__class__').__annotations__

            # Sync dict values to attributes for annotated fields
            for anno in annotations:
                if anno in self:
                    object.__setattr__(self, anno, self[anno])

        except (AttributeError, KeyError):
            pass

        return object.__getattribute__(self, item)

    def _substitute_variables(self, value):
        """Substitute ${variable} patterns with values from self"""
        if not isinstance(value, str):
            return value

        result = value
        # Find all ${variable} patterns
        import re
        pattern = r'\$\{(\w+)\}'
        matches = re.findall(pattern, value)

        for var_name in matches:
            if var_name in self:
                var_value = str(self[var_name])
                result = result.replace(f"${{{var_name}}}", var_value)
                log.debug(f"Substituted ${{{var_name}}} with '{var_value}'")
            else: raise KeyError(f"Attempted to declare variable '{var_name}' with no reference!")

        return result

    @property
    def export(self):
        """Export a clean dict with proper template field mappings"""
        exported = {}

        # Copy all existing data
        exported.update(self)

        for key in ["_redirect_uri", "_profile_pic", "_title", "_subtitle", "_card_value1", "_card_value2",
                    "_card_value3"]:
            if hasattr(self.__class__, key):
                class_value = getattr(self.__class__, key)
                # If the class value is a string that matches a key in self, use that value
                if isinstance(class_value, str) and class_value in self:
                    exported[key] = self[class_value]
                    log.debug(f"Exported {key} = '{self[class_value]}'")
                else:
                    # Apply variable substitution only to _redirect_uri
                    if key == "_redirect_uri":
                        substituted_value = self._substitute_variables(class_value)
                        exported[key] = substituted_value
                        if substituted_value != class_value:
                            log.debug(f"Exported {key} with substitution: '{class_value}' -> '{substituted_value}'")
                    else:
                        exported[key] = class_value

        return exported

    @property
    def detail(self):
        template = TEMPLATER.get_template("detail.html")
        return template.render(dict=self.export)

    @property
    def card(self):
        template = TEMPLATER.get_template("card.html")
        return template.render(dict=self.export)

    @property
    def label(self):
        template = TEMPLATER.get_template("label.html")
        return template.render(dict=self.export)

    @classmethod
    def from_pandas_row(cls, row):
        """Create HTMLDict instance from pandas Series (DataFrame row)"""
        # Convert pandas Series to dict, handling NaN values
        data = {}
        for key, value in row.items():
            if pd.isna(value):
                data[key] = None
            else:
                data[key] = value

        return cls(**data)

class Dummy(HTMLDict):
    _title = "foo"
    _subtitle = "bar"
    _redirect_uri = "http://${url}"
    foo: str
    bar: str
    url: str

if __name__ == "__main__":
    d = Dummy(foo="foo", bar="bar", url="example.com")
    p = Path("test.html")
    p.touch(exist_ok=True)
    p.write_text(d.label)