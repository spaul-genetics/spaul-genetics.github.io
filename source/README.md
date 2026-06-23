# Biography Source

This directory is the consolidated source for the biography site and PDF CV.

Edit these files:

- `data/profile.json` for biography text, education, experience, skills, links, and contact details.
- `data/publications.bib` for publications. Use `slug = {...}` to keep a stable website URL. Use `web = {false}` or `cv = {false}` when an entry should be hidden from one output.

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
