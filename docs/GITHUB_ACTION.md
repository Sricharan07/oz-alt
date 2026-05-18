# Oz GitHub Action

Use the `setup-oz` action to install Oz in CI, initialize `.codo`, and pre-pull documentation packs for agent workflows.

```yaml
jobs:
  docs-cache:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: Sricharan07/oz/.github/actions/setup-oz@v0.1.5
        with:
          auth-token: ${{ secrets.OZ_AUTH_TOKEN }}
          pull: vercel/next.js facebook/react
          search: middleware authentication cookies
          search-library: vercel/next.js
```

The action writes the API URL to the Oz config, stores the token only inside the CI job workspace, runs `oz init`, and optionally pulls libraries. Keep `pull` scoped to the libraries your repository actually uses.

For local development inside this repository, use `./.github/actions/setup-oz`.
