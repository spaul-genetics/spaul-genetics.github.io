.PHONY: all render cv site clean

SITE_URL := https://spaul-genetics.github.io/

all: site

render:
	python3 scripts/render_biography.py

cv: render
	cd CV && latexmk -pdf -interaction=nonstopmode -halt-on-error cv_all_format.tex
	cp CV/cv_all_format.pdf academic-start/static/uploads/resume.pdf

site: cv
	cd academic-start && hugo --gc --minify --baseURL "$(SITE_URL)"

clean:
	cd CV && latexmk -C cv_all_format.tex
	rm -rf academic-start/public academic-start/resources
