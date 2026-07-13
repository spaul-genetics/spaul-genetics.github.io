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

Create a folder under `academic-start/content/post/` and put an `index.md` file in it. Use the existing proteomics post as a template for the metadata at the top of the file. Markdown content, tables, code blocks, and LaTeX equations are supported.

For a fully designed standalone HTML note, place its `index.html` under `academic-start/static/notes/<note-name>/` and set `external_link: "/notes/<note-name>/"` in the companion Markdown post. The companion post supplies the Blog listing, tags, author, summary, and searchable fallback content.

Publish from the repository root:

```sh
cd ~/Documents/spaul-genetics.github.io
make publish
```

That builds everything, copies the rendered site to the repository root, commits the changes, and pushes to GitHub.
