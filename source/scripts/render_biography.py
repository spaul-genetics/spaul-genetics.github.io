#!/usr/bin/env python3
"""Render CV and Wowchemy source files from canonical data files."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = ROOT / "data" / "profile.json"
PUBLICATIONS_PATH = ROOT / "data" / "publications.bib"
CV_DIR = ROOT / "CV"
SITE_DIR = ROOT / "academic-start"


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text() == text:
        return
    path.write_text(text)


def yaml_quote(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def yaml_list(items: list[str], indent: int = 2) -> str:
    pad = " " * indent
    return "".join(f"{pad}- {yaml_quote(item)}\n" for item in items)


def yaml_block(value: str, indent: int = 4) -> str:
    pad = " " * indent
    lines = value.rstrip().splitlines() or [""]
    return "".join(f"{pad}{line}\n" for line in lines)


def latex_rows(items: list[str]) -> str:
    return "\\\\\n\t\t\t".join(items)


def latex_url_label(url: str) -> str:
    return re.sub(r"^https?://", "", url).rstrip("/")


def load_profile() -> dict:
    return json.loads(PROFILE_PATH.read_text())


def find_matching_brace(text: str, start: int) -> int:
    depth = 0
    for i in range(start, len(text)):
        char = text[i]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return i
    raise ValueError("Unbalanced BibTeX braces")


def parse_bib_entries(text: str) -> list[dict]:
    entries: list[dict] = []
    pos = 0
    while True:
        at = text.find("@", pos)
        if at == -1:
            break
        match = re.match(r"@([A-Za-z]+)\s*\{", text[at:])
        if not match:
            pos = at + 1
            continue
        entry_type = match.group(1)
        body_start = at + match.end()
        body_end = find_matching_brace(text, body_start - 1)
        body = text[body_start:body_end]
        key, fields = parse_bib_body(body)
        entries.append(
            {
                "type": entry_type,
                "key": key,
                "fields": fields,
                "raw": text[at : body_end + 1],
            }
        )
        pos = body_end + 1
    return entries


def parse_bib_body(body: str) -> tuple[str, dict[str, str]]:
    comma = body.find(",")
    if comma == -1:
        raise ValueError("BibTeX entry without key comma")
    key = body[:comma].strip()
    fields: dict[str, str] = {}
    i = comma + 1
    while i < len(body):
        while i < len(body) and body[i] in " \t\r\n,":
            i += 1
        if i >= len(body):
            break
        name_start = i
        while i < len(body) and re.match(r"[A-Za-z0-9_\-]", body[i]):
            i += 1
        name = body[name_start:i].strip().lower()
        while i < len(body) and body[i].isspace():
            i += 1
        if i >= len(body) or body[i] != "=":
            break
        i += 1
        while i < len(body) and body[i].isspace():
            i += 1
        value, i = parse_bib_value(body, i)
        fields[name] = value.strip()
    return key, fields


def parse_bib_value(body: str, i: int) -> tuple[str, int]:
    if body[i] == "{":
        start = i + 1
        end = find_matching_brace(body, i)
        return body[start:end], end + 1
    if body[i] == '"':
        i += 1
        value = []
        escaped = False
        while i < len(body):
            char = body[i]
            if char == '"' and not escaped:
                return "".join(value), i + 1
            value.append(char)
            escaped = char == "\\" and not escaped
            if char != "\\":
                escaped = False
            i += 1
        return "".join(value), i
    start = i
    while i < len(body) and body[i] != ",":
        i += 1
    return body[start:i].strip(), i


def field(entry: dict, name: str, default: str = "") -> str:
    return entry["fields"].get(name.lower(), default)


def publication_year(entry: dict) -> int:
    match = re.search(r"\d{4}", field(entry, "year"))
    return int(match.group(0)) if match else 0


def truthy_metadata(value: str, default: bool = True) -> bool:
    if not value:
        return default
    return value.strip().lower() not in {"false", "no", "0"}


def slugify(value: str) -> str:
    value = re.sub(r"(?<=[a-z])(?=\d{4})", "-", value)
    value = re.sub(r"(?<=\d{4})(?=[a-z])", "-", value)
    value = re.sub(r"[^A-Za-z0-9]+", "-", value).strip("-").lower()
    value = re.sub(r"-+", "-", value)
    return value


def publication_slug(entry: dict) -> str:
    return field(entry, "slug") or slugify(entry["key"])


def latex_to_text(value: str) -> str:
    replacements = {
        r"\&": "&",
        r"{\'o}": "ó",
        r"{\'\i}": "í",
        r"{\delta}": "δ",
        r"$\delta$": "δ",
        r"\textbf{": "",
    }
    text = value
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = text.replace("}", "")
    text = text.replace("{", "")
    text = text.replace("--", "–")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def author_list_for_web(value: str) -> list[str]:
    authors = []
    for author in re.split(r"\s+and\s+", latex_to_text(value)):
        author = author.strip()
        if not author:
            continue
        parts = [part.strip() for part in author.split(",", 1)]
        if len(parts) == 2:
            author = f"{parts[1]} {parts[0]}".strip()
        authors.append(author)
    return authors


def bib_for_web(entry: dict) -> str:
    skip = {"slug", "web", "cv"}
    lines = [f"@{entry['type']}{{{entry['key']},"]
    for name, value in entry["fields"].items():
        if name in skip:
            continue
        clean = value.replace(r"\textbf{", "").replace("}", "}") if name != "author" else latex_to_text(value)
        lines.append(f"  {name} = {{{clean}}},")
    if lines[-1].endswith(","):
        lines[-1] = lines[-1][:-1]
    lines.append("}")
    return "\n".join(lines) + "\n"


def render_cv_contacts(profile: dict) -> None:
    person = profile["person"]
    address = "\\\\\n".join(person["cv_address"])
    text = f"""\\vspace{{-3mm}}
\\parbox{{0.5\\textwidth}}{{ % First block
\\begin{{tabbing}} % Enables tabbing
%\\textbf{{{person["name"]}}}\\\\
\\textbf{{{person["role"]}}}\\\\
{person["cv_affiliation"]}\\\\
{address}\\\\
\\end{{tabbing}}}}
\\hfill % Horizontal space between the two blocks
\\parbox{{0.5\\textwidth}}{{ % Second block
\t
\\begin{{tabbing}} % Enables tabbing
\\hspace{{2.5cm}} \\= \\hspace{{2cm}} \\= \\kill % Spacing within the block
{{\\bf Mobile Phone}} \\> {person["phone"]} \\\\ % Mobile phone
{{\\bf Email}} \\> \\href{{mailto:{person["email"]}}}{{{person["email"]}}} \\\\ % Email address
{{\\bf Linkedin}}\\> \\href{{{person["linkedin"]}}}{{{latex_url_label(person["linkedin"])}}}\\\\
{{\\bf Github}}\\>\\href{{{person["github"]}}}{{{latex_url_label(person["github"])}}}
\\end{{tabbing}}}}"""
    write_text(CV_DIR / "contacts_top.tex", text)


def render_cv_experience(profile: dict) -> None:
    blocks = ["\\section{Experience:}"]
    cv_items = [item for item in profile["experience"] if item.get("show_on_cv", True)]
    for index, item in enumerate(cv_items):
        blocks.append(
            "\\jobs\n"
            f"{{{item['cv_start']}}}{{{item.get('cv_connector', '')}}}{{{item['cv_end']}}}\n"
            f"{{{item['cv_company']}}}\n"
            f"{{{item['cv_description']}}}"
        )
        if index != len(cv_items) - 1:
            blocks.append("\\vspace{-0.6cm}")
    write_text(CV_DIR / "research_new.tex", "\n\n".join(blocks) + "\n")


def render_cv_education(profile: dict) -> None:
    blocks = ["\\section{Education}", "\\vspace{-0.1in}"]
    for item in profile["education"]:
        blocks.append(
            "\\education\n"
            f"{{{item['start']}}}{{{item.get('connector', 'to')}}}{{{item['end']}}}\n"
            f"{{{item['institution']}}}\n"
            f"{{{item['degree']}}}\n"
            f"{{{item['cv_description']}}}"
        )
    blocks.append("\\vspace{0.15in}")
    write_text(CV_DIR / "education_wo_ms_du.tex", "\n\n".join(blocks) + "\n")


def render_cv_skills(profile: dict) -> None:
    cv = profile["skills"]["cv"]
    text = f"""\\section{{Skills}}
\\begin{{table}}[H]
\t\\begin{{tabular}}{{l!{{\\color{{lightgray}}\\vrule}}l !{{\\color{{stablered}}\\vrule}}  !{{\\color{{stablered}}\\vrule}} l !{{\\color{{lightgray}}\\vrule}} l}}
\t\tCore & \\begin{{minipage}}[t]{{0.25\\columnwidth}}%
\t\t\t{latex_rows(cv["core"])}
\t\t\\end{{minipage}} & \\begin{{minipage}}[t]{{0.15\\columnwidth}}%
\t\t\tProgramming \\\\Languages
\t\t\\end{{minipage}} & \\begin{{minipage}}[t]{{0.35\\columnwidth}}%
\t\t\t{latex_rows(cv["programming_languages"])}
\t\t\\end{{minipage}}\\\\ 
\t\t&\\\\
\t\tLanguages & \\begin{{minipage}}[t]{{0.28\\columnwidth}}%
\t\t\t{latex_rows(cv["languages"])}
\t\t\\end{{minipage}} & \\begin{{minipage}}[t]{{0.15\\columnwidth}}%
\t\t\tOthers
\t\t\\end{{minipage}} & \\begin{{minipage}}[t]{{0.35\\columnwidth}}%
\t\t\t{latex_rows(cv["others"])}
\t\t\\end{{minipage}}
\t\\end{{tabular}}
\\end{{table}}"""
    write_text(CV_DIR / "skills.tex", text)


def render_cv_publications(entries: list[dict]) -> None:
    by_year: dict[int, list[dict]] = defaultdict(list)
    for entry in entries:
        if truthy_metadata(field(entry, "cv"), True):
            by_year[publication_year(entry)].append(entry)
    lines = [
        "\\clearpage",
        "\\section{Publications and Posters}",
        "",
        "\\bibliographystyle{plain}",
        "\\nobibliography{../data/publications}",
        "\\begin{longtable}{L!{\\VRule}R}",
        "%\\begin{tabular}{L!{\\VRule}R}",
    ]
    for year in sorted(by_year.keys(), reverse=True):
        if not year:
            continue
        lines.append("    {\\color{white}\\hrule}")
        year_entries = by_year[year]
        for index, entry in enumerate(year_entries):
            label = str(year) if index == 0 else "    "
            spacer = "\\\\[0.35em]" if index < len(year_entries) - 1 else "\\\\"
            lines.append(f"    {label} & \\bibentry{{{entry['key']}}}{spacer}")
    lines.extend(
        [
            "\t",
            "%\\end{tabular}",
            "\\end{longtable}",
        ]
    )
    write_text(CV_DIR / "publications.tex", "\n".join(lines) + "\n")


def render_author(profile: dict) -> None:
    person = profile["person"]
    education = [item for item in profile["education"] if item.get("show_on_web", True)]
    lines = [
        "---",
        f"title: {yaml_quote(person['name'])}",
        "",
        "superuser: true",
        "",
        f"role: {yaml_quote(person['role'])}",
        "",
        "organizations:",
        f"  - name: {yaml_quote(person['web_organization'])}",
        f"    url: {yaml_quote(person['web_organization_url'])}",
        "",
        f"bio: {yaml_quote(person['short_bio'])}",
        "",
        "interests:",
        yaml_list(profile["interests"]).rstrip(),
        "",
        "education:",
        "  courses:",
    ]
    for item in education:
        lines.extend(
            [
                f"    - course: {yaml_quote(item.get('web_degree', item['degree']))}",
                f"      institution: {yaml_quote(item.get('web_institution', item['institution']))}",
                f"      year: {yaml_quote(str(item['web_year']))}",
            ]
        )
    social = [
        ("envelope", "fas", "/#contact"),
        ("twitter", "fab", person["twitter"]),
        ("graduation-cap", "fas", person["google_scholar"]),
        ("github", "fab", person["github"]),
        ("linkedin", "fab", person["linkedin"]),
        ("cv", "ai", person["resume_path"]),
    ]
    lines.extend(["", "social:"])
    for icon, icon_pack, link in social:
        lines.extend(
            [
                f"  - icon: {yaml_quote(icon)}",
                f"    icon_pack: {yaml_quote(icon_pack)}",
                f"    link: {yaml_quote(link)}",
            ]
        )
    lines.extend(["", "email: ''", "", "highlight_name: true", "---", ""])
    for paragraph in profile["bio"]["web_paragraphs"]:
        lines.extend([paragraph, ""])
    lines.append('{{< icon name="download" pack="fas" >}} Download my {{< staticref "uploads/resume.pdf" "newtab" >}}resume{{< /staticref >}}.')
    write_text(SITE_DIR / "content" / "authors" / "admin" / "_index.md", "\n".join(lines) + "\n")


def render_home_experience(profile: dict) -> None:
    lines = [
        "---",
        "widget: experience",
        "headless: true",
        "weight: 40",
        "title: Experience",
        "subtitle:",
        "date_format: Jan 2006",
        "experience:",
    ]
    for item in profile["experience"]:
        if not item.get("show_on_web", True):
            continue
        lines.extend(
            [
                f"  - title: {yaml_quote(item['title'])}",
                f"    company: {yaml_quote(item['web_company'])}",
                f"    company_url: {yaml_quote(item.get('web_company_url', ''))}",
                f"    company_logo: {yaml_quote(item.get('web_company_logo', ''))}",
                f"    location: {yaml_quote(item.get('web_location', ''))}",
                f"    date_start: {yaml_quote(item.get('web_date_start', ''))}",
                f"    date_end: {yaml_quote(item.get('web_date_end', ''))}",
                "    description: |-",
                yaml_block(item.get("web_description", ""), 6).rstrip(),
                "",
            ]
        )
    lines.extend(["design:", "  columns: '2'", "---"])
    write_text(SITE_DIR / "content" / "home" / "experience.md", "\n".join(lines) + "\n")


def render_home_skills(profile: dict) -> None:
    lines = [
        "---",
        "widget: featurette",
        "headless: true",
        "weight: 30",
        "title: Skills",
        "subtitle:",
        "feature:",
    ]
    for item in profile["skills"]["web"]:
        lines.extend(
            [
                f"  - description: {yaml_quote(item['description'])}",
                f"    icon: {yaml_quote(item['icon'])}",
                f"    icon_pack: {yaml_quote(item['icon_pack'])}",
                f"    name: {yaml_quote(item['name'])}",
            ]
        )
    lines.append("---")
    write_text(SITE_DIR / "content" / "home" / "skills.md", "\n".join(lines) + "\n")


def render_publication_pages(entries: list[dict]) -> None:
    for entry in entries:
        if not truthy_metadata(field(entry, "web"), True):
            continue
        fields = entry["fields"]
        year = publication_year(entry)
        publication = fields.get("journal") or fields.get("booktitle") or ""
        publication_type = "1" if entry["type"].lower() == "inproceedings" else "2"
        pub_dir = SITE_DIR / "content" / "publication" / publication_slug(entry)
        authors = author_list_for_web(fields.get("author", ""))
        lines = [
            "---",
            f"title: {yaml_quote(latex_to_text(fields.get('title', entry['key'])))}",
            "authors:",
        ]
        lines.extend(f"- {yaml_quote(author)}" for author in authors)
        lines.extend(
            [
                f"date: {yaml_quote(f'{year}-01-01')}",
                f"doi: {yaml_quote(latex_to_text(fields.get('doi', '')))}",
                f"publishDate: {yaml_quote(f'{year}-01-01T00:00:00Z')}",
                "publication_types:",
                f"- {yaml_quote(publication_type)}",
                f"publication: {yaml_quote('*' + latex_to_text(publication) + '*')}",
                "publication_short: ''",
                "abstract: ''",
                "summary: ''",
                "tags: []",
                "categories: []",
                "featured: false",
                "---",
            ]
        )
        write_text(pub_dir / "index.md", "\n".join(lines) + "\n")
        write_text(pub_dir / "cite.bib", bib_for_web(entry))


def main() -> None:
    profile = load_profile()
    entries = parse_bib_entries(PUBLICATIONS_PATH.read_text())
    render_cv_contacts(profile)
    render_cv_experience(profile)
    render_cv_education(profile)
    render_cv_skills(profile)
    render_cv_publications(entries)
    render_author(profile)
    render_home_experience(profile)
    render_home_skills(profile)
    render_publication_pages(entries)


if __name__ == "__main__":
    main()
