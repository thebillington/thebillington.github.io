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

def build_person_schema(profile):
    seo = profile.get("seo", {})
    schema = {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": profile["name"],
        "url": seo.get("url", ""),
        "image": seo.get("url", "") + seo.get("image", ""),
        "jobTitle": profile.get("tagline", ""),
        "description": seo.get("description", ""),
    }
    same_as = []
    links = profile.get("links", {})
    if github := links.get("github"):
        same_as.append(f"https://github.com/{github}")
    if linkedin := links.get("linkedin"):
        same_as.append(f"https://linkedin.com/in/{linkedin}")
    if same_as:
        schema["sameAs"] = same_as
    return schema


def build_llms_txt(profile, projects):
    seo = profile.get("seo", {})
    links = profile.get("links", {})
    summary = seo.get("description") or profile.get("tagline", "")
    lines = [
        f"# {profile['name']}",
        "",
        f"> {summary}",
        "",
        "## Canonical",
        "",
        f"- Portfolio: {seo.get('url', '')}",
        f"- GitHub: https://github.com/{links.get('github', '')}",
    ]
    if links.get("linkedin"):
        lines.append(f"- LinkedIn: https://linkedin.com/in/{links['linkedin']}")
    if links.get("cv"):
        lines.append(f"- CV: {links['cv']}")
    lines.extend(
        [
            "- Sponsorship: https://github.com/sponsors/thebillington",
            "",
            "## Projects",
            "",
        ]
    )
    for project in projects:
        project_links = [f"https://github.com/{project['repo']}"]
        if project.get("demo"):
            project_links.append(project["demo"])
        if project.get("video"):
            project_links.append(project["video"])
        lines.append(
            f"- **{project['name']}** ({project['year']}): {project['description']} "
            + " ".join(project_links)
        )
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "This portfolio lists open-source and personal projects by Billy Rebecchi. "
            "Project pages are the canonical source for each project; GitHub repositories "
            "contain the code and issues.",
            "",
            "Sponsorship is optional and supports maintenance of these free projects.",
        ]
    )
    return "\n".join(lines) + "\n"


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
        person_schema=build_person_schema(profile),
    )

    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "index.html").write_text(html)
    (OUTPUT / "llms.txt").write_text(build_llms_txt(profile, projects))

    base = "https://thebillington.co.uk"
    urls = [f"{base}/", f"{base}/cv/"]
    for project in projects:
        demo = project.get("demo")
        if isinstance(demo, str) and demo.startswith("https://thebillington.github.io/"):
            urls.append(demo.replace("https://thebillington.github.io/", f"{base}/"))
    seen = []
    for url in urls:
        if url not in seen:
            seen.append(url)
    sitemap = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for url in seen:
        sitemap.extend(
            [
                "  <url>",
                f"    <loc>{url}</loc>",
                "    <lastmod>2026-11-01</lastmod>",
                "  </url>",
            ]
        )
    sitemap.append("</urlset>")
    (OUTPUT / "sitemap.xml").write_text("\n".join(sitemap) + "\n")
    (OUTPUT / "robots.txt").write_text(
        "User-agent: *\n"
        "Allow: /\n"
        "\n"
        "User-agent: GPTBot\n"
        "Allow: /\n"
        "\n"
        "User-agent: ClaudeBot\n"
        "Allow: /\n"
        "\n"
        "User-agent: PerplexityBot\n"
        "Allow: /\n"
        "\n"
        "Sitemap: https://thebillington.co.uk/sitemap.xml\n"
    )
    print(f"Generated {OUTPUT / 'index.html'}")
    print(f"Generated {OUTPUT / 'llms.txt'}")
    print(f"Generated {OUTPUT / 'sitemap.xml'} and {OUTPUT / 'robots.txt'}")

if __name__ == "__main__":
    main()
