import os
import argparse
from shutil import rmtree
from urllib.parse import urljoin

from bs4 import BeautifulSoup, element
from jinja2 import Environment, FileSystemLoader, select_autoescape

import content

first_name = "Wisdom"
nickname = "wisdom"
name = "Wisdom Okechukwu"
title_name = "Wisdom Okechukwu"
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


def img_tag_rule(img_tag: element.Tag):
    if not img_tag.has_attr("decoding"):
        img_tag["decoding"] = "async"
    if not img_tag.has_attr("loading"):
        img_tag["loading"] = "lazy"


seo_common = {
    "url": url,
    "title": title_name,
    "description": content.PROFILE["description"],
    "image": urljoin(url, content.PROFILE["photo"]),
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
# Everything the pages say lives in content.py, next to the sources for its numbers.
index_soup = render_template(
    "index.html",
    name=name,
    title=title_name,
    profile=content.PROFILE,
    now=content.NOW,
    projects=content.PROJECTS,
    before=content.BEFORE,
    recognition=content.RECOGNITION,
)
for item in seotags:
    index_soup.head.append(bs(item))

write_output(index_soup.encode_contents().decode("utf-8"), "index.html")
