'''
Whether every recipe here is named what Golem will look it up by.

Golem drops the last field of an identity until something answers, so a recipe
answers to its directory name and to every identity above it. Golem composes
them, so no identity below is typed by hand.
'''

import ast
import os

import pytest

from golemcpp.golem.source_id import SourceId


COOKBOOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RECIPE_MARKER = '@'

PROJECT_FILE = 'golemfile.py'

# A dependency whose own project ships a golemfile.py needs no recipe here.
# There is none today, therefore adding an entry means adding the reason too.
DEPENDENCIES_WITHOUT_A_RECIPE = []


def recipes():
    '''
    Name every recipe directory, the way a cookbook listing selects them.

    The leading `@` is what tells a recipe from the furniture this repository
    also holds, so `tests` and `.github` never reach a caller.
    '''
    return sorted(name for name in os.listdir(COOKBOOK)
                  if name.startswith(RECIPE_MARKER)
                  and os.path.isdir(os.path.join(COOKBOOK, name)))


def declared_dependencies():
    '''
    Pair every repository a recipe declares with the recipe declaring it.

    Read off the syntax tree rather than matched in the text, so a locator
    written over two lines is still found.
    '''
    found = set()

    for recipe in recipes():
        path = os.path.join(COOKBOOK, recipe, PROJECT_FILE)

        # Parametrizing runs this at collection, therefore a recipe holding no
        # project file would error the whole suite out here and report none of
        # it. That fault belongs to the test that owns it.
        if not os.path.exists(path):
            continue

        with open(path, encoding='utf-8') as project_file:
            tree = ast.parse(project_file.read(), filename=path)

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue

            for keyword in node.keywords:
                if keyword.arg != 'repository':
                    continue
                if isinstance(keyword.value, ast.Constant):
                    found.add((recipe, keyword.value.value))

    return sorted(found)


@pytest.mark.parametrize('recipe', recipes())
def test_a_recipe_is_named_by_an_identity(recipe):
    # Spelling it back is what tells an identity from something that merely
    # starts with an `@`: reading one folds case and drops a trailing empty
    # field, so `@Json@...` and `@json@@` both come back spelled differently.
    assert str(SourceId.parse(recipe)) == recipe


@pytest.mark.parametrize('recipe', recipes())
def test_a_recipe_holds_a_project_file(recipe):
    # A directory named right and holding nothing is a recipe Golem finds and
    # then cannot load, which is worse than one it never finds.
    assert os.path.exists(os.path.join(COOKBOOK, recipe, PROJECT_FILE))


def test_no_two_recipes_name_one_identity():
    # Reading an identity folds case, therefore two directories a
    # case-sensitive filesystem keeps apart can still be one name to Golem,
    # and which of them answers would be decided by the listing order.
    by_identity = {}
    for recipe in recipes():
        by_identity.setdefault(str(SourceId.parse(recipe)), []).append(recipe)

    collisions = {name: held for name, held in by_identity.items() if len(held) > 1}

    assert collisions == {}


@pytest.mark.parametrize('recipe, repository', declared_dependencies())
def test_a_declared_dependency_finds_its_recipe(recipe, repository):
    '''
    Check a dependency a recipe declares resolves to a recipe here.

    This is the agreement itself rather than the shape of a name: what is
    reached is what a consumer reaches, by the same locator. Golem drops the
    last field of an identity until something answers, so the rung that answers
    may be shorter than the identity the locator composes.
    '''
    identity = SourceId.from_locator(repository)

    if str(identity) in DEPENDENCIES_WITHOUT_A_RECIPE:
        pytest.skip('{} ships its own project file'.format(identity))

    held = set(recipes())
    answering = [str(rung) for rung in identity.rungs() if str(rung) in held]

    assert answering, (
        "{} declares {}, which Golem looks up as '{}', and nothing here "
        "answers it at any qualification ({}). Name a recipe at one of those, "
        "or list the identity in DEPENDENCIES_WITHOUT_A_RECIPE with the "
        "reason.".format(
            recipe, repository, identity,
            ', '.join(str(rung) for rung in identity.rungs())))
