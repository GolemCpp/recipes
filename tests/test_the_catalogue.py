'''
Whether every recipe here is named what Golem will look it up by.

Golem drops the last field of an identity until something answers, so a recipe
answers to its directory name and to every identity above it. Golem composes
them, so no identity below is typed by hand.

A recipe also declares where its package is, therefore the name and the locator
have to agree: the directory is one of the identities the locator composes.
'''

import ast
import os

import pytest

from golemcpp.golem import recipe_manifest
from golemcpp.golem.recipe_manifest import RecipeManifest
from golemcpp.golem.source_id import SourceId

COOKBOOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RECIPE_MARKER = '@'

PROJECT_FILE = 'golemfile.py'

# A dependency whose own project ships a golemfile.py needs no recipe here.
# There is none today, therefore adding an entry means adding the reason too.
DEPENDENCIES_WITHOUT_A_RECIPE = []

# A recipe Golem cannot be pointed at by name, because nothing says where its
# package is. There is none today. Adding an entry means adding the reason too.
RECIPES_WITHOUT_A_LOCATOR = []


def recipes():
    '''
    Name every recipe directory, the way a cookbook listing selects them.

    The leading `@` is what tells a recipe from the furniture this repository
    also holds, so `tests` and `.github` never reach a caller.
    '''
    return sorted(
        name
        for name in os.listdir(COOKBOOK)
        if name.startswith(RECIPE_MARKER)
        and os.path.isdir(os.path.join(COOKBOOK, name))
    )


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


def manifest_of(recipe):
    '''Read what a recipe declares about itself.'''
    return RecipeManifest.read(
        recipe_manifest.recipe_manifest_path(os.path.join(COOKBOOK, recipe)),
        origin="recipe '{}'".format(recipe),
    )


def answering_rungs(identity):
    '''Name every recipe here that a lookup of identity would reach.'''
    held = set(recipes())

    return [str(rung) for rung in identity.rungs() if str(rung) in held]


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


@pytest.mark.parametrize('recipe', recipes())
def test_a_recipe_says_where_its_package_is(recipe):
    '''
    Check a recipe declares a locator, so it can be named as a location.

    A recipe reachable by name alone still builds what Golem cloned, but
    nothing can point at it by that name, which is half of what naming it was
    for.
    '''
    if recipe in RECIPES_WITHOUT_A_LOCATOR:
        pytest.skip('{} says where its package is elsewhere'.format(recipe))

    assert manifest_of(recipe).locator, (
        "{} declares no locator, therefore '{}' cannot be used as a location. "
        "Write one in {}, or list the recipe in RECIPES_WITHOUT_A_LOCATOR with "
        "the reason.".format(recipe, recipe, recipe_manifest.RECIPE_MANIFEST_FILENAME)
    )


@pytest.mark.parametrize('recipe', recipes())
def test_a_recipe_is_named_by_the_locator_it_declares(recipe):
    '''
    Check a recipe's locator agrees with the directory name identifying it.

    The locator derives to an identity, and that identity has to be served by
    this directory.

    A name shorter than the identity serves more than that one locator, which
    is what a short name is for.
    '''
    locator = manifest_of(recipe).locator

    if not locator:
        pytest.skip('{} declares no locator'.format(recipe))

    identity = SourceId.from_locator(locator)

    assert recipe in [str(rung) for rung in identity.rungs()], (
        "{} declares {}, which Golem composes as '{}'. Nothing looking that up "
        "reaches this directory, since the rungs are {}.".format(
            recipe, locator, identity, ', '.join(str(rung) for rung in identity.rungs())
        )
    )


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

    answering = answering_rungs(identity)

    assert answering, (
        "{} declares {}, which Golem looks up as '{}', and nothing here "
        "answers it at any qualification ({}). Name a recipe at one of those, "
        "or list the identity in DEPENDENCIES_WITHOUT_A_RECIPE with the "
        "reason.".format(
            recipe,
            repository,
            identity,
            ', '.join(str(rung) for rung in identity.rungs()),
        )
    )
