# Djene: Inject a Django Gene Into Your SQLModel

Tired of SQLModel's plain queries? Give your models a dose of Django's expressive querysets with Djene!

## Key Features

* **Unleash the Django Within:** Filter, order, get, and more using Django's beloved queryset API.
* **SQLModel Superpowers:** Keep all the benefits of SQLModel while writing cleaner, chainable queries.
* **Seamless Integration:** No genetic engineering required – Djene works with your existing models.
* **Evolve Your Queries:** Extend Djene's queryset behavior to adapt to your project's unique DNA.
* **FastAPI Compatibility:** Built-in middleware makes integrating with FastAPI a breeze.

**Disclaimer:** Djene is still in its experimental phase. We welcome your feedback and contributions as we work towards a stable release.

## Installation

```bash
pip install djene
```

## Usage with FastAPI (Genetic Modification Example)

```python
from fastapi import FastAPI
from sqlmodel import create_engine, Field, SQLModel
from typing import Optional

from djene import DjeneMiddleware, dj

# Database setup (replace with your actual credentials)
engine = create_engine("postgresql+psycopg2://user:password@host/database")

app = FastAPI()
app.add_middleware(DjeneMiddleware, engine=engine)

class Hero(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    name: str
    age: Optional[int] = Field(default=None)

@app.get("/hero/{hero_id}")
def get_hero(hero_id: int):
    hero = dj(Hero).get_or_none(id=hero_id)
    return hero if hero is not None else {"error": "Hero not found"}
```

## Unleash Your Inner Django

```python
# Filtering
heroes = dj(Hero).filter(age__gt=30, name__startswith="S")  # Find strong heroes over 30
heroes = dj(Hero).filter(age__in=[25, 35])                 # Heroes aged 25 or 35
heroes = dj(Hero).filter(name__isnull=True)                # Heroes with no name

# Ordering
heroes = dj(Hero).order_by("-age")                          # Rank heroes by experience (age)

# Retrieving
hero = dj(Hero).get(id=1)                                  # Get a specific hero
first_hero = dj(Hero).first()                              # Get the first hero
all_heroes = dj(Hero).all()                                # Get all heroes

# Aggregation (experimental)
oldest_hero = dj(Hero).order_by("-age").first()             # Find the oldest hero
hero_count = len(dj(Hero).all())                           # Count all heroes
```

## Documentation

We're still decoding Djene's full potential. Stay tuned for comprehensive documentation.

## Contributing

Want to help evolve Djene? Check out our [Contributing Guidelines](CONTRIBUTING.md).

## License

Djene is open-source under the MIT License, free for you to experiment and modify.