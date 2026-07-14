# Biography Source

This directory is the consolidated source for the biography site and PDF CV.

Edit these files:

- `data/profile.json` for biography text, education, experience, skills, links, and contact details.
- `data/publications.bib` for publications. Use `slug = {...}` to keep a stable website URL. Use `web = {false}` or `cv = {false}` when an entry should be hidden from one output.
- `academic-start/content/post/<post-name>/index.md` for blog posts and technical notes.

Generated files are overwritten by `scripts/render_biography.py`, including:

- `CV/contacts_top.tex`
- `CV/research_new.tex`
- `CV/education_wo_ms_du.tex`
- `CV/skills.tex`
- `CV/publications.tex`
- `academic-start/content/authors/admin/_index.md`
- `academic-start/content/home/experience.md`
- `academic-start/content/home/skills.md`
- `academic-start/content/publication/*/index.md`
- `academic-start/content/publication/*/cite.bib`

Build locally:

```sh
make all
```

That regenerates the source files, builds `CV/cv_all_format.pdf`, copies it to `academic-start/static/uploads/resume.pdf`, and builds the Hugo site in `academic-start/public/`.

## Add A Blog Post

Create matching folders with the same `<post-name>` slug:

```text
academic-start/content/post/<post-name>/index.md
academic-start/static/notes/<post-name>/index.html
```

The Markdown file can start with an H1 title and an optional italic subtitle. `scripts/prepare_blog_posts.py` automatically adds standard Hugo metadata when it is missing, connects the Blog entry to the matching HTML report, enables math, and adds a responsive “Biography & Blog” return button to HTML reports that do not already have one. Existing metadata and existing return buttons are preserved, so the script is safe to run repeatedly.

Preview locally with:

```sh
make preview
```

The preparation also runs during `make all`, `make publish`, and the GitHub Pages workflow. Markdown content, tables, code blocks, and LaTeX equations are supported.

The companion Markdown post supplies the Blog listing, tags, author, summary, and searchable fallback content. You can edit the automatically added tags and summary before committing.

Publish from the repository root:

```sh
cd ~/Documents/spaul-genetics.github.io
make publish
```

That builds everything, copies the rendered site to the repository root, commits the changes, and pushes to GitHub.
