# Golem Recipes

> **Branches:** `develop` is the default and integration branch. The recipes themselves sit on one branch per naming grammar. Each Golem reads the branch it understands:
>
> - `v2` — Golem 1.3 and later. The recipes in use.
> - `v1` / `main` — Golem 1.2 and earlier. Frozen.
>
> You do not clone this repository to use it, Golem fetches it for you (see [Usage](#usage)).

This is the default **cookbook** [Golem](https://github.com/GolemCpp/golem) searches for recipes: project files for dependencies that do not ship one of their own.

**Contributions are very welcome!** A recipe here is what makes a library usable as a Golem dependency by everyone, without each project writing the same build script again.

## Usage

Nothing to install. Golem fetches this cookbook into its cache on `golem resolve`, and looks a recipe up whenever a dependency has no `golemfile.py` of its own.

To use a cookbook of your own instead, or in addition, see [Custom cookbooks](https://golemcpp.org/docs/advanced/recipes/#custom-cookbooks). Cookbooks are layered in the order they are listed and the last one holding a recipe wins, so a cookbook of yours goes after this one to override it.

## Layout

One directory per dependency, named after the [source identity](https://golemcpp.org/docs/reference/source-identities/) of the repository it is a recipe for, each holding a `golemfile.py` and a `recipe.json`.

The leading `@` in a recipe directory name is what tells a recipe from everything else this repository holds.

The `recipe.json` says where the package is:

```json
{
  "version": 1,
  "locator": "https://github.com/boostorg/boost.git"
}
```

That is what lets a project name the package instead of its URL, writing `location='@boost'`. The directory name and the locator have to agree.

A recipe is named at the qualification that makes it unambiguous, and no further:

- `@boost`: the name alone, where nothing else goes by it.
- `@json@nlohmann`: the owner too, where more than one project shares the name.
- `@mylib@acme@gitlab.com`: the host too, where the same owner name exists on more than one.

Golem drops the last field of an identity until something answers.

## Writing a recipe

Read [Recipes](https://golemcpp.org/docs/advanced/recipes/) for what a recipe is and how it is named.

The quickest way to find the name a recipe needs is to let Golem ask for it. When no recipe matches, it names the identity it looked for, and a directory of that name is what answers.

Before opening a pull request, check your directory corresponds to the identity being looked for, and that the locator you declared composes it:

```bash
pip install golemcpp
python -m pytest tests
```

The tests use Golem itself to compose the identities and check the recipes have valid directory names. No network needed.

After `golem resolve`, Golem says which recipe served each dependency (e.g. `@json@nlohmann@github.com: served by @json@nlohmann@github.com (…)`) so you can confirm yours was reached rather than something above it.

Three worth reading before writing one:

- [@json@nlohmann/golemfile.py](@json@nlohmann/golemfile.py) — minimal header-only export.
- [@bustache/golemfile.py](@bustache/golemfile.py) — custom script-driven build.
- [@boost/golemfile.py](@boost/golemfile.py) — platform branching and generated artifacts.
