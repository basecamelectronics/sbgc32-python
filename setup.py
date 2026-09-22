"""Build configuration wheel."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from setuptools import find_packages, setup
from wheel.bdist_wheel import bdist_wheel

README = Path(__file__).with_name("README.md").read_text(encoding="utf-8")

PACKAGE_NAME = "sbgc32"
VERSION = os.environ.get("SBGC32_VERSION", "0.9.3").lstrip("v")

PROTOCOL_LIBRARY = {
    "win32": "_native/sbgc_python_protocol.dll",
    "darwin": "_native/libsbgc_python_protocol.dylib",
}.get(sys.platform, "_native/libsbgc_python_protocol.so")


class BinaryWheel(bdist_wheel):
    """The package contains a platform-specific shared library."""

    def finalize_options(self):
        super().finalize_options()
        self.root_is_pure = False

    def get_tag(self):
        _, _, platform_tag = super().get_tag()
        return "py3", "none", platform_tag


setup(
    name=PACKAGE_NAME,
    version=VERSION,
    description="Asynchronous Python interface for the SimpleBGC32 Serial API",
    long_description=README,
    long_description_content_type="text/markdown",
    python_requires=">=3.10",
    install_requires=["pyserial>=3.5"],
    author="BaseCam Electronics",
    author_email="support@basecamelectronics.com",
    license="Apache-2.0",
    url="https://github.com/basecamelectronics/sbgc32-python",
    project_urls={
        "Source": "https://github.com/basecamelectronics/sbgc32-python",
        "Issues": "https://github.com/basecamelectronics/sbgc32-python/issues",
        "SerialAPI": "https://www.basecamelectronics.com/serialapi/",
    },
    keywords=[
        "basecam",
        "simplebgc",
        "gimbal",
        "serialapi",
    ],
    package_dir={"": "src"},
    packages=find_packages("src"),
    package_data={"sbgc32": [PROTOCOL_LIBRARY]},
    cmdclass={"bdist_wheel": BinaryWheel},
)
