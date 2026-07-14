.PHONY: all prepare-blog preview publish clean

all:
	$(MAKE) -C source all

prepare-blog:
	$(MAKE) -C source prepare-blog

preview:
	$(MAKE) -C source preview

publish:
	$(MAKE) -C source publish

clean:
	$(MAKE) -C source clean
