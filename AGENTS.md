# Agent Notes

## Scope

- This folder is the default recipe catalog used by Golem for dependencies that do not ship their own Golem project file.
- It is not a standalone application. Most validation happens indirectly through a consuming project.

## Source Of Truth

- Use the recipe guide at [../golemcpp.github.io/content/docs/advanced/3-recipes.md](../golemcpp.github.io/content/docs/advanced/3-recipes.md) for semantics and naming conventions.
- For recipe loading and fallback behavior, verify against [../golem/src/golemcpp/golem/context.py](../golem/src/golemcpp/golem/context.py).

## Working Rules

- Do not assume one uniform recipe shape. Recipes may be header-only, compile sources directly, or wrap upstream build systems.
- Do not invent repo-wide build or test commands here. Recipes are normally exercised through `golem resolve`, `golem dependencies`, and `golem build` from a consumer project such as [../golem/examples](../golem/examples).
- Preserve the existing folder naming convention such as `json@com.github.nlohmann`; names are derived from repository identity.
- Keep changes minimal and recipe-local unless the task is explicitly about shared helper behavior.

## Useful Patterns

- [json@com.github.nlohmann/golemfile.py](json@com.github.nlohmann/golemfile.py): minimal header-only export recipe.
- [bustache@com.github.jamboree/golemfile.py](bustache@com.github.jamboree/golemfile.py): custom script-driven build.
- [boost@com.github.boostorg/golemfile.py](boost@com.github.boostorg/golemfile.py): complex recipe with platform branching and generated artifacts.