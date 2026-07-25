# slicap_det — optional fast determinant engine

C++/GiNaC implementation of SLiCAP's own minor-expansion determinant
algorithm with exact rational arithmetic. Used by
`det(method="MECPP")` (SLiCAP.ini: `[math] numer = MECPP`,
`denom = MECPP`). **Optional**: without it, SLiCAP computes the identical
result in Python (method "ME"), only slower — typically ~100× slower on
fully symbolic matrices.

GiNaC and CLN are GPL-licensed; this engine is a separately built
executable called by SLiCAP at arm's length (subprocess), so installing
it does not change SLiCAP's MIT licensing.

## Build & install

Linux (Debian/Ubuntu):

    sudo apt install g++ make pkg-config libginac-dev
    make && make install          # installs to ~/.local/bin/slicap_det

macOS (Homebrew):

    brew install ginac pkg-config
    make && make install

Windows (MSYS2/MinGW — CLN does not build under MSVC):

    pacman -S mingw-w64-x86_64-gcc mingw-w64-x86_64-pkg-config mingw-w64-x86_64-ginac make
    make
    # place slicap_det.exe somewhere on PATH

## Activation

SLiCAP auto-detects `slicap_det` on PATH when (re)generating
`~/SLiCAP.ini`; delete that file once after installing, or set
`[commands] slicap_det = /path/to/slicap_det` manually. Then set
`numer = MECPP` and `denom = MECPP` in the project `SLiCAP.ini`
`[math]` section. Verify with `SLiCAP.ini.dump("COMMANDS")`.

If the binary is missing or incompatible, `det(method="MECPP")` warns
once and falls back to the Python implementation — results are always
identical (`slicap_det --version` must report protocol 1).
