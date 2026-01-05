# tables.github.io
some useful to have around tables, automatically kept up to date

repo/
├── build.py              # Python script (requests + jinja2)
├── templates/
│   └── base.html.j2 + table.html.j2
├── site/
│   └── index.html + others    # GENERATED (served by GitHub Pages)
└── .github/workflows/
    └── build.yml         # runs Python on push
