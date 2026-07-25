CXX      = g++
CXXFLAGS = -O2 -std=c++17 $(shell pkg-config --cflags ginac)
LIBS     = $(shell pkg-config --libs ginac)

slicap_det: det_cli.cpp
	$(CXX) $(CXXFLAGS) -o $@ $< $(LIBS)

install: slicap_det
	install -D slicap_det $(HOME)/.local/bin/slicap_det

clean:
	rm -f slicap_det

.PHONY: install clean
