"""Download and read cached rule packages."""

import hashlib
import io
import json
import os
import re
import tempfile
from pathlib import Path, PurePosixPath
from urllib.request import HTTPRedirectHandler, Request, build_opener
from zipfile import BadZipFile, ZipFile

from slop_away.cmds.helpers.packages import (
    PackageSpec,
    check_members,
    check_transport,
    parse_package,
)
from slop_away.cmds.helpers.rules.schema import read_rule
from slop_away.utils.exceptions import PackageError

MB = 1024 * 1024
MAX_DOWNLOAD = 16 * MB
MAX_EXPANDED = 64 * MB
MAX_RULE = 1 * MB


class PackageRedirect(HTTPRedirectHandler):
    """Check package download redirects."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        """Check a redirected request.

        Args:
            req: The source request.
            fp: The response stream.
            code: The response code.
            msg: The response message.
            headers: The response headers.
            newurl: The redirect URL.

        Returns:
            The checked request.
        """
        check_transport(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _rules(archive: ZipFile, names: set[str], package: str) -> dict[str, bytes]:
    """Read package rule files.

    Args:
        archive: The package archive.
        names: The archive file names.
        package: The package name.

    Returns:
        The rule file names and data.

    Raises:
        PackageError: Rule files are absent or ambiguous.
    """
    roots = [
        f"{package}/",
        f"styles/{package}/",
        f"{package}/styles/{package}/",
    ]
    groups = []
    for root in roots:
        members = {
            name
            for name in names
            if name.startswith(root)
            and "/" not in name[len(root) :]
            and PurePosixPath(name).suffix.lower() in {".yml", ".yaml"}
        }
        if members:
            groups.append((root, members))
    if len(groups) != 1:
        raise PackageError("Expected exactly one package rule directory.")
    root, members = groups[0]
    if any(
        name.startswith(root)
        and "/" in name[len(root) :]
        and PurePosixPath(name).suffix.lower() in {".yml", ".yaml"}
        for name in names
    ):
        raise PackageError("Nested rule directories are unsupported.")
    result = {}
    stems = set()
    for name in sorted(members):
        filename = name[len(root) :]
        stem = PurePosixPath(filename).stem
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_.-]*", stem) or stem in stems:
            raise PackageError(f"Invalid or duplicate rule name {filename!r}.")
        stems.add(stem)
        if archive.getinfo(name).file_size > MAX_RULE:
            raise PackageError(f"Rule {name} exceeds the size limit.")
        source = archive.read(name)
        read_rule(f"{package}.{stem}", source)
        result[filename] = source
    return result


def _download(spec: PackageSpec) -> bytes:
    """Download a package archive.

    Args:
        spec: The package source.

    Returns:
        The archive data.

    Raises:
        PackageError: The download exceeds the size limit.
    """
    request = Request(spec.url, headers={"User-Agent": "slop_away"})
    with build_opener(PackageRedirect()).open(request, timeout=30) as response:
        data = response.read(MAX_DOWNLOAD + 1)
    if len(data) > MAX_DOWNLOAD:
        raise PackageError("Package exceeds the download size limit.")
    return data


def _cache(spec: PackageSpec) -> bytes:
    """Prepare a checked package cache.

    Args:
        spec: The package source.

    Returns:
        The cache archive.
    """
    data = _download(spec)
    with ZipFile(io.BytesIO(data)) as archive:
        rules = _rules(archive, check_members(archive), spec.name)
    manifest = {
        "version": 1,
        "url": spec.url,
        "archive_sha256": hashlib.sha256(data).hexdigest(),
        "rules": {
            name: hashlib.sha256(source).hexdigest() for name, source in rules.items()
        },
    }
    output = io.BytesIO()
    with ZipFile(output, "w") as archive:
        archive.writestr("manifest.json", json.dumps(manifest, sort_keys=True))
        for name, source in rules.items():
            archive.writestr(f"rules/{name}", source)
    return output.getvalue()


def sync_packages(config) -> None:
    """Download and cache the configured packages.

    Args:
        config: The project settings.

    Raises:
        PackageError: A package cannot be downloaded or checked.
    """
    pending = []
    for url in config.packages:
        spec = parse_package(url)
        try:
            pending.append((spec, _cache(spec)))
        except (OSError, ValueError, BadZipFile, RuntimeError) as e:
            raise PackageError(f"{spec.name}: {e}") from e
    if not pending:
        return
    packages_dir = config.root / ".slop_away" / "packages"
    packages_dir.mkdir(parents=True, exist_ok=True)
    for spec, data in pending:
        temp: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(dir=packages_dir, delete=False) as f:
                temp = Path(f.name)
                f.write(data)
            os.replace(temp, packages_dir / f"{spec.name}.zip")
        finally:
            if temp is not None:
                temp.unlink(missing_ok=True)
