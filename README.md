# owizdom.github.io

My personal site, built with a custom static site generator.

Template from [sagarreddypatil/portfolio-website](https://github.com/sagarreddypatil/portfolio-website),
adapted from [adv-andrew/andrewvu.me](https://github.com/adv-andrew/andrewvu.me). MIT licensed.

## Dependencies

```
pnpm install
uv sync
```

Images are stored in Git LFS, so you also need `git lfs install` once.
Image optimization needs `cwebp` (`brew install webp`).

## Development

```
uv run python src/build.py --output dist
pnpm dev
```

## Production

```
pnpm build
```

Output lands in `dist/`. Pushing to `main` triggers `.github/workflows/deploy.yml`,
which builds and publishes to GitHub Pages.

## Map

```
owizdom.github.io
├── README.md
├── dist                          # output directory (gitignored)
├── LICENSE                       # MIT
├── package.json                  # JS deps & dev server target
├── tailwind.config.js
├── pyproject.toml                # Python deps
├── build.sh                      # prod build, called by pnpm build
├── public
│   └── assets/                   # static assets, icons, images
└── src
    ├── build.py                  # main entrypoint, renders the one page
    ├── content.py                # everything the page says, plus the claims ledger
    ├── dev-server.py             # live reload server
    ├── index.css                 # tailwind imports
    ├── optimize_images.py
    └── templates
        └── index.html            # the whole site, one plain page
```

## Editing content

The page is data-driven from `src/content.py`: `PROFILE`, `NOW`, `BEFORE`,
`PROJECTS` and `RECOGNITION`. Identity (name, domain, handles) is the block at
the top of `src/build.py`.
