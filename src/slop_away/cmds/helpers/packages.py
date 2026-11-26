"""Download and read cached rule packages."""

import hashlib
import io
import ipaddress
import json
import os
import re
import stat
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
from zipfile import BadZipFile, ZipFile

from slop_away.cmds.helpers.rules.schema import Rule, read_rule
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


def check_members(archive: ZipFile) -> set[str]:
    """Check archive members.

    Args:
        archive: The package archive.

    Returns:
        The archive file names.

    Raises:
        PackageError: A member is unsafe or exceeds a limit.
    """
    infos = archive.infolist()
    if len(infos) > 4096 or sum(item.file_size for item in infos) > MAX_EXPANDED:
        raise PackageError("Package exceeds the archive size limits.")
    names: set[str] = set()
    files: set[str] = set()
    for item in infos:
        path = PurePosixPath(item.filename)
        if (
            path.is_absolute()
            or ".." in path.parts
            or "\\" in item.filename
            or item.filename in names
            or "\x00" in item.filename
            or stat.S_ISLNK(item.external_attr >> 16)
        ):
            raise PackageError(f"Invalid archive member {item.filename!r}.")
        names.add(item.filename)
        if not item.is_dir():
            files.add(item.filename)
    return files


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
        except (OSError, ValueError, BadZipFile, RuntimeError) as error:
            raise PackageError(f"{spec.name}: {error}") from error
    if not pending:
        return
    directory = config.root / ".slop_away" / "packages"
    directory.mkdir(parents=True, exist_ok=True)
    for spec, data in pending:
        temporary: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(dir=directory, delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(data)
            os.replace(temporary, directory / f"{spec.name}.zip")
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)


def check_transport(url: str) -> None:
    """Check a package transport URL.

    Args:
        url: The download URL.

    Raises:
        ValueError: The URL does not use an allowed transport.
    """
    parsed = urlsplit(url)
    host = parsed.hostname
    if not host or parsed.username is not None or parsed.password is not None:
        raise ValueError("Package URLs need a host and must omit credentials.")
    if parsed.port == 0:
        raise ValueError("Package URLs need a valid port.")
    if parsed.scheme == "https":
        return
    loopback = host == "localhost"
    if not loopback:
        try:
            loopback = ipaddress.ip_address(host).is_loopback
        except ValueError:
            loopback = False
    if parsed.scheme != "http" or not loopback:
        raise ValueError("Use HTTPS package URLs; HTTP needs a loopback host.")


@dataclass(frozen=True)
class PackageSpec:
    """Hold a package name and its source URL."""

    name: str
    url: str


def parse_package(url: str) -> PackageSpec:
    """Read a package name from its URL.

    Args:
        url: The package ZIP URL.

    Returns:
        The package name and source URL.

    Raises:
        ValueError: The URL or package name is invalid.
    """
    check_transport(url)
    parsed = urlsplit(url)
    path = PurePosixPath(unquote(parsed.path))
    if parsed.fragment or path.suffix.lower() != ".zip":
        raise ValueError("Package URLs must name ZIP files and omit fragments.")
    name = path.stem
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,127}", name):
        raise ValueError("Package names need letters, digits, '_' or '-'.")
    return PackageSpec(name, url)


def _load(spec: PackageSpec, root: Path) -> tuple[Rule, ...]:
    """Read one package cache.

    Args:
        spec: The package source.
        root: The project directory.

    Returns:
        The package rules.

    Raises:
        PackageError: The cache is missing or invalid.
    """
    path = root / ".slop_away" / "packages" / f"{spec.name}.zip"
    try:
        with ZipFile(path) as archive:
            names = check_members(archive)
            if archive.getinfo("manifest.json").file_size > MAX_RULE:
                raise PackageError("Cache manifest exceeds the size limit.")
            manifest = json.loads(archive.read("manifest.json"))
            if (
                not isinstance(manifest, dict)
                or type(manifest.get("version")) is not int
                or manifest.get("version") != 1
                or manifest.get("url") != spec.url
                or not isinstance(manifest.get("archive_sha256"), str)
                or not re.fullmatch(r"[0-9a-f]{64}", manifest["archive_sha256"])
            ):
                raise PackageError("Cache source or version does not match.")
            hashes = manifest.get("rules")
            if (
                not isinstance(hashes, dict)
                or not hashes
                or any(not isinstance(name, str) for name in hashes)
            ):
                raise PackageError("Invalid cache rule list.")
            if names != {"manifest.json"} | {f"rules/{name}" for name in hashes}:
                raise PackageError("Cache members do not match the manifest.")
            rules = []
            for name, digest in sorted(hashes.items()):
                if (
                    PurePosixPath(name).name != name
                    or PurePosixPath(name).suffix.lower() not in {".yml", ".yaml"}
                    or not re.fullmatch(
                        r"[A-Za-z][A-Za-z0-9_.-]*", PurePosixPath(name).stem
                    )
                ):
                    raise PackageError("Invalid cache rule name.")
                if archive.getinfo(f"rules/{name}").file_size > MAX_RULE:
                    raise PackageError("Cached rule exceeds the size limit.")
                source = archive.read(f"rules/{name}")
                if hashlib.sha256(source).hexdigest() != digest:
                    raise PackageError(f"Cache hash does not match {name}.")
                rules.append(
                    read_rule(f"{spec.name}.{PurePosixPath(name).stem}", source)
                )
            return tuple(rules)
    except (OSError, ValueError, KeyError, BadZipFile, RuntimeError) as e:
        raise PackageError(f"{spec.name}: {e}. Run slop_away sync.") from e


def load_rules(config) -> tuple[Rule, ...]:
    """Read configured rules without network access.

    Args:
        config: The project settings.

    Returns:
        The configured rules.

    Raises:
        PackageError: A cache or rule selector is invalid.
    """
    rules = tuple(
        rule
        for url in config.packages
        for rule in _load(parse_package(url), config.root)
    )
    codes = {rule.code for rule in rules}
    selectors = list(config.select or []) + config.ignore
    for profile in config.profiles.values():
        selectors.extend(profile.get("select", []))
        selectors.extend(profile.get("ignore", []))
    for ignored in config.per_file_ignores.values():
        selectors.extend(ignored)
    for selector in selectors:
        if "." in selector and selector not in codes:
            raise PackageError(f"Unknown package rule selector {selector!r}.")
    return rules
