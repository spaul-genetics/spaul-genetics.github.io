# Subrata Paul's Biography Site and CV

This repository contains both the public GitHub Pages site and the source files used to generate it.

## What To Edit

For normal updates, edit only these files:

- `source/data/profile.json` for biography text, education, experience, skills, contact information, and links.
- `source/data/publications.bib` for publications.

The generated website files and PDF CV are rebuilt automatically by GitHub Actions after you push changes to `main`.

## Update The Website And CV Automatically

From this repository folder:

```sh
cd ~/Documents/spaul-genetics.github.io
git add source/data/profile.json source/data/publications.bib
git commit -m "Update profile data"
git push origin main
```

After the push, GitHub Actions runs `.github/workflows/build-pages.yml`. The workflow:

1. Regenerates the CV and website source files from `profile.json` and `publications.bib`.
2. Builds the PDF CV.
3. Copies the new PDF to `uploads/resume.pdf`.
4. Rebuilds the Hugo website.
5. Deploys the rendered website to GitHub Pages.

You can watch progress in the repository's **Actions** tab. GitHub Pages usually refreshes the public website within a few minutes after the workflow succeeds.

## Local Publish Fallback

The automatic GitHub Actions workflow is the preferred update path. If you need to rebuild, commit, and push everything from this computer instead, run:

```sh
cd ~/Documents/spaul-genetics.github.io
make publish
```

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

## GitHub Actions Notes

1. Workflow file: `.github/workflows/build-pages.yml`
1. Trigger: pushes to `main` that change `source/**` or the workflow file itself.
1. Manual run: open the **Actions** tab, choose **Build CV and GitHub Pages**, then click **Run workflow**.
1. GitHub Pages should be configured with **Build and deployment** > **Source** set to **GitHub Actions**.
