"""Build gate: filename, installer version resource, portable and frozen runtime agree."""

import hashlib
import sys
import zipfile
from pathlib import Path

import pefile

from sistela.version import VERSION


def verify(installer: Path, portable: Path):
    if installer.name != f"SISTELA-Assistant-Setup-{VERSION}.exe":
        raise ValueError("Installer filename differs from canonical version")
    if portable.name != f"SISTELA-Assistant-Portable-{VERSION}.zip":
        raise ValueError("Portable filename differs from canonical version")
    with pefile.PE(str(installer)) as pe:
        info = pe.VS_FIXEDFILEINFO[0]
        version = (
            info.ProductVersionMS >> 16,
            info.ProductVersionMS & 65535,
            info.ProductVersionLS >> 16,
            info.ProductVersionLS & 65535,
        )
        if version != (*map(int, VERSION.split(".")), 0):
            raise ValueError("Installer version resource differs from canonical version")
    executable = installer.parent / "SISTELA-Assistant/SISTELA-Assistant.exe"
    with zipfile.ZipFile(portable) as archive:
        packaged = archive.read("SISTELA-Assistant/SISTELA-Assistant.exe")
    if hashlib.sha256(packaged).digest() != hashlib.sha256(executable.read_bytes()).digest():
        raise ValueError("Portable executable differs from frozen runtime")
    # This starts the real EXE with an isolated database and asserts /app/info,
    # plus both production PDF imports. No developer Python service substitutes it.
    from smoke_windows import main

    main()


if __name__ == "__main__":
    verify(Path(sys.argv[1]), Path(sys.argv[2]))
