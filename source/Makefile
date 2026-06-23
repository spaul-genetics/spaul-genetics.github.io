.PHONY: all render cv site publish clean

SITE_URL := https://spaul-genetics.github.io/
COMMIT_MESSAGE ?= Update biography site

all: site

render:
	python3 scripts/render_biography.py

cv: render
	cd CV && latexmk -pdf -interaction=nonstopmode -halt-on-error cv_all_format.tex
	cp CV/cv_all_format.pdf academic-start/static/uploads/resume.pdf

site: cv
	cd academic-start && hugo --gc --minify --baseURL "$(SITE_URL)"

publish: site
	rsync -a --delete --exclude .git --exclude .github --exclude source --exclude README.md --exclude Makefile academic-start/public/ ../
	git -C .. add -A -- . ':!.github'
	@if git -C .. diff --cached --quiet; then \
		echo "No changes to publish."; \
	else \
		git -C .. commit -m "$(COMMIT_MESSAGE)"; \
		git -C .. push origin main; \
	fi

clean:
	cd CV && latexmk -C cv_all_format.tex
	rm -rf academic-start/public academic-start/resources
