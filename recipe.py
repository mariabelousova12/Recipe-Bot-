from typing import Callable

from category import category_of_recipe
from db import Database
from func_types import Recipe, Category


def left_or_target_recipe(db: Database, target: Recipe) -> Recipe:
    def inside():
        left = db.connection().execute('SELECT id FROM recipe WHERE category=? AND id<? ORDER BY id DESC',
                                       (category_of_recipe(db, target)(), target())).fetchone()
        return (left and left[0]) or target()

    return inside


def right_or_target_recipe(db: Database, target: Recipe) -> Recipe:
    def inside():
        right = db.connection().execute('SELECT id FROM recipe WHERE category=? AND id>? ORDER BY id',
                                        (category_of_recipe(db, target)(), target())).fetchone()
        return (right and right[0]) or target()

    return inside


def first_recipe_in_category(db: Database, category: Category) -> Recipe:
    def inside():
        row = db.connection().execute('SELECT id FROM recipe WHERE category=? ORDER BY id',
                                      (category(),)).fetchone()
        if not row:
            raise Exception(f'Category {category()} do not contains any recipe')
        return row[0]

    return inside


def recipe_text(db: Database, recipe: Recipe) -> Callable[[], str]:
    return lambda: \
        db.connection().execute('SELECT recipe FROM recipe WHERE id=?', (recipe(),)).fetchone()[0]


def recipe_name(db: Database, recipe: Recipe) -> Callable[[], str]:
    return lambda: \
        db.connection().execute('SELECT name FROM recipe WHERE id=?', (recipe(),)).fetchone()[0]
