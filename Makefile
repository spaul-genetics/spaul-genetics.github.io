.PHONY: all publish clean

all:
	$(MAKE) -C source all

publish:
	$(MAKE) -C source publish

clean:
	$(MAKE) -C source clean
