#!/usr/bin/env python3
import yaml
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

ROOT = Path(__file__).parent
DATA = ROOT / "data"
TEMPLATES = ROOT / "templates"
OUTPUT = ROOT / "docs"

def load_yaml(path):
    with open(path) as f:
        return yaml.safe_load(f)

def main():
    profile = load_yaml(DATA / "profile.yml")
    projects_data = load_yaml(DATA / "projects.yml")

    featured = projects_data.get("featured", [])
    all_projects = projects_data.get("projects", [])

    featured.sort(key=lambda p: p["year"], reverse=True)
    all_projects.sort(key=lambda p: p["year"], reverse=True)

    env = Environment(loader=FileSystemLoader(TEMPLATES))
    template = env.get_template("index.html")

    html = template.render(
        profile=profile,
        featured=featured,
        projects=all_projects,
    )

    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "index.html").write_text(html)
    print(f"Generated {OUTPUT / 'index.html'}")

if __name__ == "__main__":
    main()
