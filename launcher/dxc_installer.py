# SPDX-License-Identifier: AGPL-3.0-only
"""Optional DirectX Shader Compiler (dxcompiler.dll + dxil.dll) for DirectX 12.

With the two DLLs beside mh3u-tools.exe, DirectX 12 compiles the game's shaders in seconds instead of
tens of seconds (without them it uses the slow FXC compiler). They are Microsoft's, released by
microsoft/DirectXShaderCompiler under the Microsoft Software License Terms in LICENSE-MS.txt, so the
launcher does not ship them: the player reads the terms (assets/dxc_license_ms.txt), accepts, and only
then are they downloaded from Microsoft's own release. Only those files are read from the zip (HTTP
Range requests) and each one is checked against the sha256 pinned here.
"""

import hashlib
import os
import shutil
import tempfile
import urllib.request
import zipfile

try:
    import toolchain_installer
except Exception:  # without it the whole zip is downloaded
    toolchain_installer = None

RELEASE = "v1.9.2609"
URL = f"https://github.com/microsoft/DirectXShaderCompiler/releases/download/{RELEASE}/dxc_2026_09_29.zip"
LICENSE_URL = "https://github.com/microsoft/DirectXShaderCompiler/blob/main/LICENSE-MS.txt"
# member of the zip -> (file name beside mh3u-tools.exe, sha256)
FILES = {
    "bin/x64/dxcompiler.dll": ("dxcompiler.dll", "0689e2fee0a1c9df8662a59680469f24e2a3ad7ce6bbbcc9284f7a83172bfc59"),
    "bin/x64/dxil.dll": ("dxil.dll", "64be2368211d257a038a7d4ea6bb3e24c878eb8d588c7b8414fccf759b69c2ac"),
    "LICENSE-MS.txt": ("dxc_LICENSE-MS.txt", "734f72f239fe7b07b4c7203f294c1a7ce27095687278bab7e56d630d7c672963"),
}
DLLS = ("dxcompiler.dll", "dxil.dll")
LICENSE_ASSET = "dxc_license_ms.txt"


class DxcError(Exception):
    pass


def installed(base_dir):
    return all(os.path.isfile(os.path.join(base_dir, n)) for n in DLLS)


def license_text(assets_dir):
    try:
        with open(os.path.join(assets_dir, LICENSE_ASSET), "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return ""


def _open_zip(source, log):
    """(zipfile, cleanup): a local path, or the remote zip read with Range requests (whole download if unsupported)."""
    if os.path.isfile(source):
        return zipfile.ZipFile(source), lambda: None
    if toolchain_installer:
        try:
            return zipfile.ZipFile(toolchain_installer.RangeFile(source)), lambda: None
        except OSError as e:
            log(f"Descarga parcial no disponible ({e}); se baja el paquete completo.")
    tmp = tempfile.mkdtemp(prefix="mh3u_dxc_")
    path = os.path.join(tmp, "dxc.zip")
    req = urllib.request.Request(source, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r, open(path, "wb") as out:
        shutil.copyfileobj(r, out)
    return zipfile.ZipFile(path), lambda: shutil.rmtree(tmp, ignore_errors=True)


def install(base_dir, progress=lambda f: None, log=lambda m: None, source=URL, files=None):
    """Download the DLLs and the license into base_dir. Raises DxcError (nothing half-written is left behind)."""
    files = files or FILES
    written = []
    try:
        zf, cleanup = _open_zip(source, log)
    except Exception as e:
        raise DxcError(f"No se pudo abrir el paquete de Microsoft: {e}")
    try:
        total = sum(zf.getinfo(m).file_size for m in files) or 1
        done = 0
        for member, (name, digest) in files.items():
            try:
                data = zf.read(member)
            except Exception as e:
                raise DxcError(f"No se pudo leer {member}: {e}")
            if hashlib.sha256(data).hexdigest() != digest:
                raise DxcError(f"{name}: la suma sha256 no coincide con la esperada; no se instala.")
            dest = os.path.join(base_dir, name)
            part = dest + ".part"
            try:
                with open(part, "wb") as f:
                    f.write(data)
                os.replace(part, dest)
            except OSError as e:
                try:
                    os.remove(part)
                except OSError:
                    pass
                raise DxcError(f"No se pudo escribir {name} (¿el juego está abierto?): {e}")
            written.append(dest)
            done += len(data)
            progress(min(done / total, 1.0))
            log(f"Instalado {name}")
    finally:
        zf.close()
        cleanup()
    return written
