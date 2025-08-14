A lightweight Python class that extends dict to generate HTML templates and integrate with databases.

### Usage

```python
from pathlib import Path
from core import HTMLDict, Database

class Person(HTMLDict):
    _title = "name"
    _subtitle = "role" 
    _redirect_uri = "https://profile/${id}"
    name: str
    role: str
    id: str

# Create instance
person = Person(name="John Doe", role="Developer", id="123")

# Generate HTML
html_card = person.card
html_detail = person.detail
html_label = person.label

# Save to database
class DB(Database):
    person: Person

db = DB("mydb")
person.commit_to_database(db)
```