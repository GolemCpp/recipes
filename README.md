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

One directory per dependency, named after the [source identity](https://golemcpp.org/docs/reference/source-identities/) of the repository it is a recipe for, each holding a `golemfile.py`.

The leading `@` in a recipe directory name is what tells a recipe from everything else this repository holds.

## Writing a recipe

Read [Recipes](https://golemcpp.org/docs/advanced/recipes/) for what a recipe is and how it is named.

The quickest way to find the name a recipe needs is to let Golem ask for it. When no recipe matches, it names the identity it looked for, and a directory of that name is what answers.

Three worth reading before writing one:

- [@json@nlohmann@github.com/golemfile.py](@json@nlohmann@github.com/golemfile.py) — minimal header-only export.
- [@bustache@jamboree@github.com/golemfile.py](@bustache@jamboree@github.com/golemfile.py) — custom script-driven build.
- [@boost@boostorg@github.com/golemfile.py](@boost@boostorg@github.com/golemfile.py) — platform branching and generated artifacts.
