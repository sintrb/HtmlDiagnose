# -*- coding: utf-8 -*-
import os, io
from setuptools import setup

from HtmlDiagnose.HtmlDiagnose import __version__
here = os.path.abspath(os.path.dirname(__file__))
README = io.open(os.path.join(here, 'README.rst'), encoding='UTF-8').read()
CHANGES = io.open(os.path.join(here, 'CHANGES.rst'), encoding='UTF-8').read()
setup(name='HtmlDiagnose',
      version=__version__,
      description='A weeb page HTML format diagnoser.',
      long_description=README + '\n\n\n' + CHANGES,
      url='https://github.com/sintrb/HtmlDiagnose',
      classifiers=[
          'Intended Audience :: Developers',
          'Operating System :: OS Independent',
          'Programming Language :: Python :: 2.7',
          'Topic :: Text Editors',
      ],
      keywords='HtmlDiagnose HTML',
      author='sintrb',
      author_email='sintrb@gmail.com',
      license='Apache',
      packages=['HtmlDiagnose'],
      scripts=['HtmlDiagnose/HtmlDiagnose', 'HtmlDiagnose/HtmlDiagnose.bat'],
      include_package_data=True,
      zip_safe=False)
