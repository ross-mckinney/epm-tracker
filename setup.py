"""
setup.py
"""

DESCRIPTION = 'Package for tracking and analyzing Elevated Plus Maze (EPM) data.'
VERSION = '0.1.1'
DISTNAME = 'epm-tracker'
AUTHOR = 'Ross McKinney'
AUTHOR_EMAIL = 'ross.m.mckinney@gmail.com'
LICENSE = 'MIT'

REQUIRED_PACKAGES = {
    'pandas': 'pandas',
    'scipy': 'scipy',
    'skimage': 'skimage',
    'matplotlib': 'matplotlib',
    'PyQt4': 'PyQt4',
    'qdarkstyle': 'qdarkstyle',
    'numpy': 'numpy',
    'motmot.FlyMovieFormat.FlyMovieFormat': 'motmot.FlyMovieFormat>=0.5.9.1'
}

try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup

def check_dependencies():
    """Make sure all necessary packages are present."""
    install = []
    for key, value in REQUIRED_PACKAGES.iteritems():
        try:
            module = __import__(key)
        except ImportError:
            install.append(value)

    return install

if __name__ == '__main__':
    install_requires = check_dependencies()

    setup(
        name=DISTNAME,
        author=AUTHOR,
        author_email=AUTHOR_EMAIL,
        maintainer=AUTHOR,
        maintainer_email=AUTHOR_EMAIL,
        description=DESCRIPTION,
        license=LICENSE,
        version=VERSION,
        install_requires=install_requires,
        packages=[
                'epm'
            ],
        package_data={'epm': ['icons/*.png']},
        entry_points="""
            [console_scripts]
            epm-tracker=epm.entry:launch_gui
        """
    )
