# thebillington.github.io

Personal portfolio site. Generated from YAML data files using Python + Jinja2.

## Usage

```bash
pip install -r requirements.txt
python3 generate.py
```

Output goes to `docs/` which is served by GitHub Pages.

## Layout

- `data/`: the profile and project list, in YAML.
- `templates/`: the Jinja2 page templates and `style.css`.
- `docs/`: generated output. Do not edit by hand.
- `og/`: the Open Graph card and its screenshots.
