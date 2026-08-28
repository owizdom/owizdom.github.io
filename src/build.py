import os
import argparse
from shutil import rmtree
from urllib.parse import urljoin

import mistune
import frontmatter
from bs4 import BeautifulSoup, element
from jinja2 import Environment, FileSystemLoader, select_autoescape

first_name = "Wisdom"
nickname = "wisdom"
name = "Wisdom"
title_name = "Wisdom"
domain = "owizdom.github.io"
generic_username = "owizdom"
twitter_username = "@oxwizzdom"
url = f"https://{domain}"  # for opengraph


def bs(content):
    return BeautifulSoup(content, "html.parser")


parser = argparse.ArgumentParser(description="Build the website")
parser.add_argument("--output", help="Output directory", default="dist")
parser.add_argument(
    "--no-clean", help="Don't clean the output directory", action="store_true"
)

args = parser.parse_args()

script_path = os.path.dirname(os.path.realpath(__file__))

env = Environment(
    loader=FileSystemLoader(f"{script_path}/templates"),
    autoescape=select_autoescape(["html"]),
)

if not args.no_clean:
    # delete everything inside the output directory
    for root, dirs, files in os.walk(args.output):
        for file in files:
            if file == "index.css":
                continue
            os.remove(os.path.join(root, file))

        for dir in dirs:
            rmtree(os.path.join(root, dir))


def write_output(content, *path):
    # make sure every directory in the path exists
    for i in range(len(path) - 1):
        if not os.path.exists(os.path.join(args.output, *path[: i + 1])):
            os.makedirs(os.path.join(args.output, *path[: i + 1]))

    with open(os.path.join(args.output, *path), "w", encoding="utf-8") as f:
        f.write(content)


def render_template(template_name, **context):
    template = env.get_template(template_name)
    rendered = template.render(**context)
    soup = bs(rendered)

    for img_tag in soup.find_all("img"):
        img_tag_rule(img_tag)

    return soup


make_html: mistune.Markdown = mistune.create_markdown(
    escape=False,
    plugins=["strikethrough", "footnotes", "table", "speedup", "math"],
)


def get_post(folder, file):
    obj = frontmatter.load(f"posts/{folder}/{file}")
    html = make_html(obj.content)

    obj.content = html
    obj["slug"] = file.replace(".md", "")
    obj["href"] = f"/{folder}/{obj['slug']}"

    if "order" not in obj:
        obj["order"] = 0

    return obj


def og_tags(data: dict):
    tags = []
    for key, value in data.items():
        tags.append(f'<meta property="og:{key}" content="{value}">')

    if "description" in data:
        tags.append(f'<meta name="description" content="{data["description"]}">')

    return tags


twitter_tags_common = {
    "domain": domain,
    "card": "summary_large_image",
    "site": twitter_username,
}


def twitter_tags(data: dict):
    lut = {
        "card": "name",
        "domain": "property",
        "url": "property",
        "title": "name",
        "description": "name",
        "image": "name",
        "site": "name",
    }

    data = {**twitter_tags_common, **data}

    tags = []
    for key, value in data.items():
        tags.append(f'<meta {lut[key]}="twitter:{key}" content="{value}">')

    return tags


def post_seotags(folder, post):
    items_common = {
        "url": urljoin(url, f"/{folder}/{post['slug']}"),
    }

    if "title" in post:
        items_common["title"] = f"{name} | {post['title']}"

    if "summary" in post:
        items_common["description"] = post["summary"]

    if "coverImage" in post:
        items_common["image"] = urljoin(url, post["coverImage"])

    items_og = {
        **items_common,
        "type": "website",
    }

    items_twitter = {
        **items_common,
        "card": "summary_large_image",
        "domain": domain,
    }

    return og_tags(items_og) + twitter_tags(items_twitter)


def render_post(folder, post):
    template = env.get_template(f"posts/{folder}/page.html")
    rendered = template.render(post=post, title=f"{name} | {post['title']}", name=name)

    soup = bs(rendered)
    og = post_seotags(folder, post)

    for item in og:
        soup.head.append(bs(item))

    return soup.encode_contents().decode("utf-8")


def render_post_list(folder, posts):
    template = env.get_template(f"posts/{folder}/list.html")
    return template.render(posts=posts)


post_folders = [f for f in os.listdir("posts") if os.path.isdir(f"posts/{f}")]
lists = {}

for post_folder in post_folders:
    post_files = os.listdir(f"posts/{post_folder}")
    posts = [get_post(post_folder, f) for f in post_files]
    posts = sorted(posts, key=lambda x: x["order"])

    for post in posts:
        write_output(
            render_post(post_folder, post), post_folder, f"{post['slug']}.html"
        )

    lists[post_folder] = render_post_list(post_folder, posts)


def img_tag_rule(img_tag: element.Tag):
    if not img_tag.has_attr("decoding"):
        img_tag["decoding"] = "async"
    if not img_tag.has_attr("loading"):
        img_tag["loading"] = "lazy"


seo_common = {
    "url": url,
    "title": title_name,
    "description": f"{title_name}'s personal website",
    "image": urljoin(url, "/assets/me.jpg"),
}

og = og_tags(
    {
        **seo_common,
        "type": "profile",
        "profile:first_name": first_name,
        "profile:username": generic_username,
    }
)

twitter = twitter_tags({**seo_common, "card": "summary"})
seotags = og + twitter

# ---------------------------------------------------------------- site content
experience = [
    {"logo": "/assets/experience/freesystems.png",
     "org": "Free Systems Lab, Stanford GSB", "role": "Member of Technical Staff",
     "note": "working on the politics of superintelligence",
     "href": "https://freesystems.net/", "starred": True},
    {"logo": "/assets/experience/coinbase.png",
     "org": "Coinbase", "role": "User Research",
     "note": "working with product & engineering teams",
     "href": "https://www.coinbase.com/", "starred": True},
    {"logo": "/assets/experience/bento.png",
     "org": "Bento", "role": "Software Engineer",
     "note": "building the sdk, resolution, and agentic layers for prediction markets",
     "href": "https://bento.fun", "starred": True},
    {"logo": "/assets/experience/eigenlabs.png",
     "org": "EigenLabs", "role": "Open-Source Contributor",
     "note": "protocol tooling and client work",
     "href": "https://www.eigenlabs.org", "starred": False},
    {"logo": "/assets/experience/astral.png",
     "org": "Astral Protocol", "role": "Research Engineer",
     "note": "building toward a decentralized geospatial web",
     "href": "https://astral.global", "starred": False},
    {"logo": "/assets/experience/shoal.png",
     "org": "Shoal Research", "role": "Researcher",
     "note": "deep dives and thesis-driven reports",
     "href": "https://shoal.gg/", "starred": False},
    {"logo": "/assets/experience/decentralised.png",
     "org": "decentralised.co", "role": "Researcher",
     "note": "tools and charts serving 30k+ users",
     "href": "https://www.decentralised.co/", "starred": False},
    {"logo": "/assets/experience/parallel.png",
     "org": "Parallel Research", "role": "Head of Research",
     "note": "long-form writing on solana, plasma, and zk",
     "href": "https://parallelresearch.substack.com/", "starred": True},
]

projects = [
    {"name": "swarm mind", "starred": True,
     "desc": "An autonomous prediction oracle. Three AI agents independently analyze crypto "
             "markets, seal their predictions with TEE hardware keys before seeing each "
             "other's work, then reveal simultaneously to produce a verifiable consensus.",
     "links": [{"label": "GitHub", "href": "https://github.com/owizdom/swarm_mind_for_PredMarkets"}]},
    {"name": "bobIsAlive", "starred": True,
     "desc": "An autonomous digital organism that must earn to survive. It reads biology news, "
             "makes art, completes tasks, trades on DeFi and stakes STRK, all inside an "
             "EigenCompute TEE. If its balance hits zero, it dies. No human bailout.",
     "links": [{"label": "GitHub", "href": "https://github.com/owizdom/bobIsAlive"},
               {"label": "Site", "href": "https://bob-is-alive.vercel.app"}]},
    {"name": "model card explorer", "starred": False,
     "desc": "Benchmark-disclosure transparency across published AI model cards.",
     "links": [{"label": "GitHub", "href": "https://github.com/owizdom/ai-research-model-cards"},
               {"label": "Site", "href": "https://modelcards.net"}]},
    {"name": "sticky fingers", "starred": False,
     "desc": "Does payment-authorization architecture contain a misbehaving AI agent? A "
             "controlled experiment across today's agentic-payment protocols, with the model, "
             "prompt, task, tools and attack held constant so the architecture is the only "
             "thing that varies.",
     "links": [{"label": "GitHub", "href": "https://github.com/owizdom/sticky-Fingers"}]},
]


index_soup = render_template(
    "index.html",
    lists=lists,
    name=name,
    title=title_name,
    experience=experience,
    projects=projects,
)
for item in seotags:
    index_soup.head.append(bs(item))

write_output(index_soup.encode_contents().decode("utf-8"), "index.html")

custom_pages = [
    {
        "template": "random/wins.html",
        "output": ("random", "wins.html"),
        "title": f"{title_name} | Wins",
        "seo": {
            **seo_common,
            "url": urljoin(url, "/random/wins"),
            "title": f"{title_name} | Wins",
            "description": f"{title_name}'s trophy case of wins and milestones",
            "image": urljoin(url, "/assets/me.jpg"),
        },
    },
    {
        "template": "random/toolbox.html",
        "output": ("random", "toolbox.html"),
        "title": f"{title_name} | Toolbox",
        "seo": {
            **seo_common,
            "url": urljoin(url, "/random/toolbox"),
            "title": f"{title_name} | Toolbox",
            "description": f"{title_name}'s stack turned into a tiny tetris-style toolbox game",
            "image": urljoin(url, "/assets/me.jpg"),
        },
    },
    {
        "template": "resources.html",
        "output": ("resources.html",),
        "title": f"{title_name} | Resources",
        "seo": {
            **seo_common,
            "url": urljoin(url, "/resources"),
            "title": f"{title_name} | Resources",
            "description": f"{title_name}'s shelf of resources for visitors from videos and posts",
            "image": urljoin(url, "/assets/me.jpg"),
        },
    },
]

for page in custom_pages:
    soup = render_template(page["template"], name=name, title=page["title"])
    page_tags = og_tags({**page["seo"], "type": "website"}) + twitter_tags(page["seo"])

    for item in page_tags:
        soup.head.append(bs(item))

    write_output(soup.encode_contents().decode("utf-8"), *page["output"])
