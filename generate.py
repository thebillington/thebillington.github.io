#!/usr/bin/env python3
import yaml
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

ROOT = Path(__file__).parent
DATA = ROOT / "data"
TEMPLATES = ROOT / "templates"
OUTPUT = ROOT / "docs"

SECTION_ORDER = ["featured", "games", "apps"]
SECTION_TITLES = {
    "featured": "Featured",
    "games": "Games",
    "apps": "Apps & Tools",
}

def load_yaml(path):
    with open(path) as f:
        return yaml.safe_load(f)

def main():
    profile = load_yaml(DATA / "profile.yml")
    projects = load_yaml(DATA / "projects.yml")

    by_category = {}
    for p in projects:
        cat = p.get("category", "other")
        by_category.setdefault(cat, []).append(p)

    sections = []
    for cat in SECTION_ORDER:
        items = by_category.get(cat, [])
        if cat != "featured":
            items.sort(key=lambda p: p["year"], reverse=True)
        sections.append({
            "key": cat,
            "title": SECTION_TITLES[cat],
            "projects": items,
        })

    env = Environment(loader=FileSystemLoader(TEMPLATES))
    template = env.get_template("index.html")

    html = template.render(
        profile=profile,
        sections=sections,
    )

    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "index.html").write_text(html)
    print(f"Generated {OUTPUT / 'index.html'}")

if __name__ == "__main__":
    main()
