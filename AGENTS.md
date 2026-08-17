# Agent Notes

## Scope

- This folder is the default cookbook used by Golem: the catalog of recipes for dependencies that do not ship their own Golem project file.
- It is not a standalone application. Most validation happens indirectly through a consuming project.

## Source Of Truth

- Use the recipe guide at [../golemcpp.github.io/content/docs/advanced/3-recipes.md](../golemcpp.github.io/content/docs/advanced/3-recipes.md) for semantics and naming conventions.
- For recipe loading and fallback behavior, verify against [../golem/src/golemcpp/golem/context.py](../golem/src/golemcpp/golem/context.py).

## Working Rules

- Do not assume one uniform recipe shape. Recipes may be header-only, compile sources directly, or wrap upstream build systems.
- Do not invent repo-wide build or test commands here. Recipes are normally exercised through `golem resolve`, `golem dependencies`, and `golem build` from a consumer project such as [../golem/examples](../golem/examples).
- Preserve the existing folder naming convention such as `json@com.github.nlohmann`; names are derived from repository identity.
- Keep changes minimal and recipe-local unless the task is explicitly about shared helper behavior.
- **Write comments and docstrings plainly.** Start a function docstring with a verb, in the imperative: `Build the library and export its headers.`. Keep one idea per sentence, mark the step with `therefore`, `so` or `but`, and use the words Golem and the upstream build system already use. Explain why a recipe does something unusual, which is what the next reader cannot work out from the code. The full rules are in the `Writing Code` section of [../golem/AGENTS.md](../golem/AGENTS.md).

## Useful Patterns

- [json@com.github.nlohmann/golemfile.py](json@com.github.nlohmann/golemfile.py): minimal header-only export recipe.
- [bustache@com.github.jamboree/golemfile.py](bustache@com.github.jamboree/golemfile.py): custom script-driven build.
- [boost@com.github.boostorg/golemfile.py](boost@com.github.boostorg/golemfile.py): complex recipe with platform branching and generated artifacts.