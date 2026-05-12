import os
import sys
import requests

TOKEN = os.environ.get("GITHUB_TOKEN")
USERNAME = "Greninja110"

HEADERS = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

SKIP_EXTENSIONS = {
    "css", "html", "scss", "sass", "less",
    "svg", "png", "jpg", "jpeg", "gif", "ico", "woff", "woff2", "ttf",
}

COLOR_MAP = {
    "Python":     "#3572A5",
    "Jupyter Notebook": "#DA5B0B",
    "Java":       "#b07219",
    "Kotlin":     "#A97BFF",
    "JavaScript": "#f1e05a",
    "TypeScript": "#2b7489",
    "C++":        "#f34b7d",
    "C":          "#555555",
    "Solidity":   "#AA6746",
    "Dart":       "#00B4AB",
    "PHP":        "#4F5D95",
    "Shell":      "#89e051",
    "Go":         "#00ADD8",
    "Ruby":       "#701516",
    "Rust":       "#dea584",
    "Swift":      "#F05138",
    "R":          "#198CE7",
}

DEFAULT_COLORS = [
    "#00B4D8", "#0077B6", "#023E8A", "#48CAE4",
    "#90E0EF", "#ADE8F4", "#CAF0F8", "#03045E",
]

IGNORED_LANGUAGES = {
    "csv", "tsv", "json", "xml", "yaml", "toml",
    "text", "markdown", "tex", "makefile", "dockerfile",
    "html", "css", "scss", "sass", "less",
}

def get_all_repos():
    repos, page = [], 1
    while True:
        res = requests.get(
            "https://api.github.com/user/repos",
            headers=HEADERS,
            params={"per_page": 100, "page": page, "affiliation": "owner"}
        )
        data = res.json()
        if not data or isinstance(data, dict):
            break
        repos.extend(data)
        page += 1
    return repos

def get_repo_languages(owner, repo):
    res = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/languages",
        headers=HEADERS
    )
    if res.status_code == 200:
        return res.json()
    return {}

def aggregate_languages(repos):
    totals = {}
    for repo in repos:
        name = repo["name"]
        langs = get_repo_languages(USERNAME, name)
        for lang, bytes_count in langs.items():
            if lang.lower() in IGNORED_LANGUAGES:
                continue
            totals[lang] = totals.get(lang, 0) + bytes_count
    return totals

def fmt_bytes(b):
    if b >= 1_000_000:
        return f"{b / 1_000_000:.1f} MB"
    if b >= 1_000:
        return f"{b / 1_000:.1f} KB"
    return f"{b} B"

def generate_svg(lang_totals):
    if not lang_totals:
        print("No language data found.")
        sys.exit(1)

    total_bytes = sum(lang_totals.values())
    sorted_langs = sorted(lang_totals.items(), key=lambda x: x[1], reverse=True)[:12]
    top_total = sum(b for _, b in sorted_langs)

    width = 480
    bar_height = 8
    row_height = 30
    padding_x = 20
    padding_top = 55
    label_col = 130
    bar_start = label_col + 10
    bar_max_width = width - bar_start - padding_x - 110
    pct_col = width - padding_x - 60
    size_col = width - padding_x - 5

    svg_height = padding_top + len(sorted_langs) * row_height + 20

    color_index = 0
    rows = []
    for i, (lang, bytes_count) in enumerate(sorted_langs):
        pct = bytes_count / top_total * 100
        bar_width = max(2, int(pct / 100 * bar_max_width))
        y = padding_top + i * row_height
        color = COLOR_MAP.get(lang)
        if not color:
            color = DEFAULT_COLORS[color_index % len(DEFAULT_COLORS)]
            color_index += 1

        dot_y = y + bar_height / 2 + 4
        rows.append(f'''
  <circle cx="{padding_x + 6}" cy="{dot_y}" r="5" fill="{color}"/>
  <text x="{padding_x + 16}" y="{dot_y + 4}" font-size="12" fill="#cdd9e5" font-family="monospace">{lang}</text>
  <rect x="{bar_start}" y="{y}" width="{bar_width}" height="{bar_height}" rx="4" fill="{color}" opacity="0.85"/>
  <text x="{pct_col}" y="{dot_y + 4}" font-size="11" fill="#8b949e" font-family="monospace" text-anchor="end">{pct:.1f}%</text>
  <text x="{size_col}" y="{dot_y + 4}" font-size="11" fill="#444d56" font-family="monospace" text-anchor="end">{fmt_bytes(bytes_count)}</text>''')

    svg = f'''<svg width="{width}" height="{svg_height}" xmlns="http://www.w3.org/2000/svg">
  <rect width="{width}" height="{svg_height}" rx="10" fill="#0d1117"/>
  <text x="{padding_x}" y="26" font-size="14" fill="#00B4D8" font-family="monospace" font-weight="bold">Most Used Languages</text>
  <text x="{padding_x}" y="40" font-size="10" fill="#8b949e" font-family="monospace">{fmt_bytes(total_bytes)} total · {len(repos)} repos</text>
  <text x="{pct_col}" y="40" font-size="10" fill="#444d56" font-family="monospace" text-anchor="end">share</text>
  <text x="{size_col}" y="40" font-size="10" fill="#444d56" font-family="monospace" text-anchor="end">size</text>
{"".join(rows)}
</svg>'''

    return svg

repos = get_all_repos()
print(f"Fetched {len(repos)} repos")

lang_totals = aggregate_languages(repos)
print(f"Languages found: {list(lang_totals.keys())}")

svg = generate_svg(lang_totals)

with open("metrics.languages.svg", "w") as f:
    f.write(svg)

print("Saved metrics.languages.svg")
