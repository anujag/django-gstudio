import os
from setuptools import setup, find_packages

import gstudio

setup(name='django-gstudio',
      version=gstudio.__version__,

      description='A collaborative blogspace for constructing and publishing semantic knowledge networks and ontologies',
      long_description='\n'.join([open('README.rst').read(),
                                  open(os.path.join('docs', 'install.rst')).read(),
                                  open(os.path.join('docs', 'changelog.rst')).read(),]),
      keywords='django, blog, weblog, zinnia, post, news, gnowsys, gnowledge, semantic, networks, ontolgies',

      author=gstudio.__author__,
      author_email=gstudio.__email__,
      url=gstudio.__url__,

      packages=find_packages(exclude=['demo']),
      classifiers=[
          'Framework :: Django',
          'Development Status :: 2 - Development/Pre-Alpha',
          'Environment :: Web Environment',
          'Programming Language :: Python',
          'Intended Audience :: Developers',
          'Operating System :: OS Independent',
          'License :: OSI Approved :: BSD License',
          'Topic :: Software Development :: Libraries :: Python Modules',],

      license=gstudio.__license__,
      include_package_data=True,
      zip_safe=False,
      install_requires=['BeautifulSoup>=3.2.0',
                        'django-mptt>=0.4.2',
                        'django-tagging>=0.3.1',
                        'django-xmlrpc>=0.1.3',
                        'pyparsing>=1.5.5',
                        'django-reversioin>=1.5.1',
                        ])
