from typing import Callable

from db import Database
from func_types import Category, Recipe


def category_of_recipe(db: Database, recipe: Recipe) -> Category:
    return lambda: \
        db.connection().execute('SELECT category FROM recipe WHERE id=?', (recipe(),)).fetchone()[0]


def category_with_title(db: Database, name: str) -> Category:
    def inside():
        row = (db.connection()
               .execute('SELECT id FROM category WHERE name = ?', (name,)).fetchone())
        if not row:
            raise Exception(f'Category with name {name} do not exists')
        return row[0]

    return inside


def has_recipes(db: Database, category: Category) -> Callable[[], bool]:
    return lambda: \
        bool(db.connection().execute('SELECT EXISTS(SELECT id FROM recipe WHERE category = ?)',
                                     (category(),)).fetchone()[0])


def exists_category_with_name(db, name) -> Callable[[], bool]:
    return lambda: \
        bool(db.connection().execute('SELECT EXISTS(SELECT id FROM category WHERE name = ?)',
                                     (name,)).fetchone()[0])
