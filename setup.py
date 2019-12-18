# -*- coding: utf-8 -*-
from setuptools import setup
import os, io

from HtmlDiagnose.HtmlDiagnose import __version__, __description__

here = os.path.abspath(os.path.dirname(__file__))
README = io.open(os.path.join(here, 'README.md'), encoding='UTF-8').read()
CHANGES = io.open(os.path.join(here, 'CHANGES.md'), encoding='UTF-8').read()
setup(name='HtmlDiagnose',
      version=__version__,
      description=__description__,
      long_description=README + '\n\n\n' + CHANGES,
      long_description_content_type="text/markdown",
      url='https://github.com/sintrb/HtmlDiagnose',
      keywords=('HtmlDiagnose', 'HTML', 'Web'),
      author='sintrb',
      author_email='sintrb@gmail.com',
      license='Apache',
      packages=['HtmlDiagnose'],
      scripts=[],
      install_requires=['requests'],
      include_package_data=True,
      zip_safe=False)
