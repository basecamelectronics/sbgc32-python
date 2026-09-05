"""Build configuration for the native-c and pyserial wheel variants."""

from __future__ import annotations

import os
import sys

from setuptools import find_packages, setup
from wheel.bdist_wheel import bdist_wheel


WHEEL_BACKEND = os.environ.get("SBGC32_WHEEL_BACKEND", "native_c")
VERSION = os.environ.get("SBGC32_VERSION", "0.9.0").lstrip("v")

PROFILES = {
    "native_c": {
        "name": "sbgc32-native-c",
        "dependencies": [],
        "native_file": "_native/sbgc_python.dll",
    },
    "pyserial": {
        "name": "sbgc32-pyserial",
        "dependencies": ["pyserial>=3.5"],
        "native_file": {
            "win32": "_native/sbgc_python_pyserial.dll",
            "darwin": "_native/libsbgc_python_pyserial.dylib",
        }.get(sys.platform, "_native/libsbgc_python_pyserial.so"),
    },
}

try:
    PROFILE = PROFILES[WHEEL_BACKEND]
except KeyError as error:
    choices = ", ".join(PROFILES)
    raise SystemExit(f"Unknown SBGC32_WHEEL_BACKEND={WHEEL_BACKEND!r}; use {choices}.") from error

if WHEEL_BACKEND == "native_c" and sys.platform != "win32":
    raise SystemExit("The native_c wheel can only be built on Windows.")


class BinaryWheel(bdist_wheel):
    """The package contains a platform-specific shared library."""

    def finalize_options(self):
        super().finalize_options()
        self.root_is_pure = False

    def get_tag(self):
        _, _, platform_tag = super().get_tag()
        return "py3", "none", platform_tag


setup(
    name=PROFILE["name"],
    version=VERSION,
    description="Python bindings for the SimpleBGC32 Serial API",
    python_requires=">=3.10",
    install_requires=PROFILE["dependencies"],
    package_dir={"": "src"},
    packages=find_packages("src"),
    package_data={"sbgc32": [PROFILE["native_file"]]},
    cmdclass={"bdist_wheel": BinaryWheel},
)
