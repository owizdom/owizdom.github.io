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
├── posts
│   └── projects                  # markdown project posts
├── public
│   └── assets/                   # static assets, icons, images
└── src
    ├── build.py                  # main entrypoint; site content lives here
    ├── dev-server.py             # live reload server
    ├── index.css                 # tailwind imports
    ├── optimize_images.py
    └── templates
        ├── components/           # button, fieldset
        ├── index.html            # landing page
        ├── layout.html           # base layout (header, footer, theme)
        ├── resources.html
        └── random/               # lore, toolbox, wins
```

## Editing content

Most of the landing page is data-driven from `src/build.py`: the `experience`,
`projects`, and `writing` lists near the bottom of the file. Identity (name,
domain, handles) is the block at the top.
