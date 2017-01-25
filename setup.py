try:
	from setuptools import setup
except ImportError:
	from distutils.core import setup

long_desc = """
	A command line tool to disaggregate pre and post test responses into Walstad and Wagner learning types
"""


setup(name="ww_out",
      version=1.3,
      description="A command line tool to disaggregate pre and post test responses into Walstad and Wagner learning types",
      author="Ben Smith",
      author_email="bosmith@unomaha.edu",
      url="https://github.com/tazzben/WW",
      license="MIT",
      packages=[],
      scripts=['ww_out'],
      package_dir={},
      long_description=long_desc,
      classifiers=[
          'Topic :: Text Processing',
          'Environment :: Console',
          'Development Status :: 5 - Production/Stable',
          'Operating System :: POSIX',
          'Intended Audience :: Developers',
          'Intended Audience :: End Users/Desktop'
      ]
     )