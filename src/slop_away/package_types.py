"""Describe configured rule packages."""

import ipaddress
import re
from dataclasses import dataclass
from pathlib import PurePosixPath
from urllib.parse import unquote, urlsplit


class PackageError(ValueError):
    """Report an invalid or unavailable rule package."""


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
        raise ValueError(
            "Package URLs must name ZIP files and omit fragments."
        )
    name = path.stem
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,127}", name):
        raise ValueError("Package names need letters, digits, '_' or '-'.")
    return PackageSpec(name, url)
