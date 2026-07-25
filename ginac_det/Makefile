# Dev/benchmark harness. The canonical engine source ships with the
# package: ../SLiCAP/files/ginac_det/ (see SLiCAP_GiNAC.md).
SRC      = ../SLiCAP/files/ginac_det/det_cli.cpp
CXX      = g++
CXXFLAGS = -O2 -std=c++17 $(shell pkg-config --cflags ginac)
LIBS     = $(shell pkg-config --libs ginac)

slicap_det: $(SRC)
	$(CXX) $(CXXFLAGS) -o $@ $< $(LIBS)

install: slicap_det
	install -D slicap_det $(HOME)/.local/bin/slicap_det

clean:
	rm -f slicap_det

.PHONY: install clean
