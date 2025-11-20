#!/usr/bin/env python3
import re
import sys
from datetime import date

import packaging.version

CHANGELOG_HEADER = "############\n Change Log\n############\n\n"
UNRELEASED_HEADER = "************\n Unreleased\n************\n\n"


def add_unreleased_to_changelog():
    """Add unreleased section to changelog.

    :returns: ``True`` if successful, ``False`` otherwise.

    """
    with open("CHANGES.rst") as fp:
        content = fp.read()

    if not content.startswith(CHANGELOG_HEADER):
        sys.stderr.write("Unexpected CHANGES.rst header\n")
        return False
    new_header = f"{CHANGELOG_HEADER}{UNRELEASED_HEADER}"
    if content.startswith(new_header):
        sys.stderr.write("CHANGES.rst already contains Unreleased header\n")
        return False

    with open("CHANGES.rst", "w") as fp:
        fp.write(f"{new_header}{content[len(CHANGELOG_HEADER) :]}")
    return True


def handle_unreleased():
    """Handle unreleased version updates.

    :returns: A boolean indicating success.

    """
    return add_unreleased_to_changelog() and increment_development_version()


def handle_version(version):
    """Handle version updates.

    :param version: Version string to set.

    :returns: A boolean indicating success.

    """
    version = valid_version(version)
    if not version:
        return False
    return update_changelog(version) and update_package(version)


def increment_development_version():
    """Increment development version number.

    :returns: A boolean indicating success.

    """
    with open("docstrfmt/__init__.py") as fp:
        version = re.search('__version__ = "([^"]+)"', fp.read()).group(1)

    parsed_version = valid_version(version)
    if not parsed_version:
        return False

    if parsed_version.is_devrelease:
        pre = "".join(str(x) for x in parsed_version.pre) if parsed_version.pre else ""
        new_version = f"{parsed_version.base_version}{pre}.dev{parsed_version.dev + 1}"
    elif parsed_version.is_prerelease:
        new_version = f"{parsed_version}.dev0"
    else:
        assert parsed_version.base_version == version
        new_version = f"{parsed_version.major}.{parsed_version.minor}.{parsed_version.micro + 1}.dev0"

    assert valid_version(new_version)
    return update_package(new_version)


def main():
    """Main entry point for version setting script."""
    if len(sys.argv) != 2:
        sys.stderr.write(f"Usage: {sys.argv[0]} VERSION\n")
        return 1
    if sys.argv[1] == "Unreleased":
        return not handle_unreleased()
    return not handle_version(sys.argv[1])


def update_changelog(version):
    """Update changelog with new version.

    :param version: Version string to add.

    :returns: A boolean indicating success.

    """
    with open("CHANGES.rst") as fp:
        content = fp.read()

    expected_header = f"{CHANGELOG_HEADER}{UNRELEASED_HEADER}"
    if not content.startswith(expected_header):
        sys.stderr.write("CHANGES.rst does not contain Unreleased header.\n")
        return False

    date_string = date.today().strftime("%Y/%m/%d")
    version_line = f" {version} ({date_string})\n"
    version_header = f"{'*' * len(version_line)}\n{version_line}{'*' * len(version_line)}\n\n"

    with open("CHANGES.rst", "w") as fp:
        fp.write(f"{CHANGELOG_HEADER}{version_header}{content[len(expected_header) :]}")
    return True


def update_package(version):
    """Update package version in __init__.py.

    :param version: Version string to set.

    :returns: A boolean indicating success.

    """
    with open("docstrfmt/__init__.py") as fp:
        content = fp.read()

    updated = re.sub('__version__ = "([^"]+)"', f'__version__ = "{version}"', content)
    if content == updated:
        sys.stderr.write("Package version string not changed\n")
        return False

    with open("docstrfmt/__init__.py", "w") as fp:
        fp.write(updated)

    print(version)
    return True


def valid_version(version):
    """Validate version string.

    :param version: Version string to validate.

    :returns: Parsed version object if valid, None otherwise.

    """
    parsed_version = packaging.version.parse(version)
    if parsed_version.local or parsed_version.is_postrelease or parsed_version.epoch:
        sys.stderr.write("epoch, local postrelease version parts are not supported")
        return False
    return parsed_version


if __name__ == "__main__":
    sys.exit(main())
