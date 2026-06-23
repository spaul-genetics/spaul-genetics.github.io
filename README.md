# Subrata Paul's Biography Site and CV

This repository contains both the public GitHub Pages site and the source files used to generate it.

## What To Edit

For normal updates, edit only these files:

- `source/data/profile.json` for biography text, education, experience, skills, contact information, and links.
- `source/data/publications.bib` for publications.

The generated website files in the repo root and the generated CV fragments in `source/CV/` are rebuilt automatically by the command below.

## Update The Website And CV

From this repository folder:

```sh
cd ~/Documents/spaul-genetics.github.io
make publish
```

That one command:

1. Regenerates the CV and website source files from `profile.json` and `publications.bib`.
2. Builds the PDF CV.
3. Copies the new PDF to `uploads/resume.pdf`.
4. Rebuilds the Hugo website.
5. Copies the rendered website into the repository root.
6. Commits the changes.
7. Pushes the changes to GitHub.

GitHub Pages usually refreshes the public website within a few minutes after the push.

## Build Without Publishing

To check that everything builds without committing or pushing:

```sh
cd ~/Documents/spaul-genetics.github.io
make all
```

The rendered site will be in `source/academic-start/public/`.

## Publications

Add new papers to:

```text
source/data/publications.bib
```

Optional fields used by the generator:

- `slug = {...}` keeps the publication page URL stable.
- `web = {false}` hides an entry from the website.
- `cv = {false}` hides an entry from the PDF CV.

BibTeX ignores these extra fields, so they are safe to keep in the shared `.bib` file.

## Note About GitHub Actions

The repository currently uses the local `make publish` workflow. A future improvement is to add a GitHub Actions workflow so GitHub rebuilds everything automatically, but that requires a GitHub credential with permission to update workflow files.
