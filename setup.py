from distutils.core import setup

with open("README.md") as f:
    long_desc = f.read()

dependencies = ["py4web", "yatl", "pydal", "configurable-json"]

setup(
    name="py4web-debug-tools",
    version="0.2.0",
    description="Debug Tools for py4web",
    author="Robin van der Noord",
    author_email="contact@trialandsuccess.nl",
    url="https://github.com/trialandsuccess/py4web-debug-tools",
    packages=["py4web_debug"],
    include_package_data=True,
    package_data={"py4web_debug": ["templates/*.html"]},
    long_description=long_desc,
    long_description_content_type="text/markdown",
    install_requires=dependencies,
    python_requires=">3.10.0",
)
