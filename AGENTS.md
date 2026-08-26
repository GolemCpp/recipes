# Agent Notes

## Scope

- This folder is the default cookbook used by Golem: the catalog of recipes for dependencies that do not ship their own Golem project file.
- It is not a standalone application. Most validation happens indirectly through a consuming project.

## Source Of Truth

- Use the recipe guide at [../golemcpp.github.io/content/docs/advanced/3-recipes.md](../golemcpp.github.io/content/docs/advanced/3-recipes.md) for semantics and naming conventions.
- For the grammar a recipe directory is named in, and the cases the guide leaves out, read [../golemcpp.github.io/content/docs/reference/3-source-identities.md](../golemcpp.github.io/content/docs/reference/3-source-identities.md).
- For recipe loading and fallback behavior, verify against [../golem/src/golemcpp/golem/context.py](../golem/src/golemcpp/golem/context.py).

## Working Rules

- Do not assume one uniform recipe shape. Recipes may be header-only, compile sources directly, or wrap upstream build systems.
- Do not invent repo-wide build or test commands here. Recipes are normally exercised through `golem resolve`, `golem dependencies`, and `golem build` from a consumer project such as [../golem/examples](../golem/examples).
- A recipe directory is named after the source identity Golem composes from the dependency's repository URL, `@<name>@<owner>@<host>` for a forge: `https://github.com/nlohmann/json.git` is `@json@nlohmann@github.com`. Never spell one by hand from a URL that is not that shape, because a field Golem could not spell safely carries a digest; ask Golem instead, which names the identity it looked for whenever no recipe answers.
- The leading `@` is what tells a recipe from everything else this repository holds, therefore a directory without one is furniture and is never loaded as a recipe.
- Keep changes minimal and recipe-local unless the task is explicitly about shared helper behavior.
- **Write comments and docstrings plainly.** Start a function docstring with a verb, in the imperative: `Build the library and export its headers.`. Keep one idea per sentence, mark the step with `therefore`, `so` or `but`, and use the words Golem and the upstream build system already use. Explain why a recipe does something unusual, which is what the next reader cannot work out from the code. The full rules are in the `Writing Code` section of [../golem/AGENTS.md](../golem/AGENTS.md).

## Useful Patterns

- [@json@nlohmann@github.com/golemfile.py](@json@nlohmann@github.com/golemfile.py): minimal header-only export recipe.
- [@bustache@jamboree@github.com/golemfile.py](@bustache@jamboree@github.com/golemfile.py): custom script-driven build.
- [@boost@boostorg@github.com/golemfile.py](@boost@boostorg@github.com/golemfile.py): complex recipe with platform branching and generated artifacts.