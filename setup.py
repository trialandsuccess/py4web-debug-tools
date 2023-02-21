from distutils.core import setup

with open('README.md') as f:
    long_desc = f.read()

with open('requirements.txt') as f:
    dependencies = f.read().split('\n')

setup(
    name='py4web-debug-tools',
    version='0.1.0',
    description='Debug Tools for py4web',
    author='Robin van der Noord',
    author_email='contact@trialandsuccess.nl',
    url='https://github.com/trialandsuccess/py4web-debug-tools',
    packages=['py4web_debug'],
    long_description=long_desc,
    long_description_content_type="text/markdown",
    install_requires=dependencies,
    python_requires='>3.10.0',
)
