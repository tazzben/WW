try:
	from setuptools import setup
except ImportError:
	from distutils.core import setup

long_desc = """
A command line tool to disaggregate Scantron or ZipGrade pre- and post-test responses into Walstad & Wagner learning types (Walstad and Wagner 2016) and adjusts them for guessing (Smith and Wagner 2017).  Usage instructions can be found at https://github.com/tazzben/WW.
"""


setup(name="ww_out",
      version=2.1,
      description="A command line tool to disaggregate Scantron or ZipGrade pre- and post-test responses into Walstad & Wagner learning types (Walstad and Wagner 2016) and adjusts them for guessing (Smith and Wagner 2017).",
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
