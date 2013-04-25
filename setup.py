try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name='armarius',
    packages=['armarius'],
    description='a personal wiki',
    author='Jae-Myoung Yu',
    author_email='euphoris@gmail.com',
    maintainer='Jae-Myoung Yu',
    maintainer_email='euphoris@gmail.com',
    url='http://github.com/euphoris/armarius',
    tests_require=['pytest'],
    install_requires=['flask', 'SQLAlchemy', 'beautifulsoup4', 'chardet'],
    )
