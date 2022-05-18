#!/usr/bin/env python
from setuptools import find_packages, setup
packages = find_packages()

with open("README.md", "r") as fh:
    long_description = fh.read()


VERSION = "1.2.16"
setup(name='python-seispy',
      version=VERSION,
      author='Mijian Xu',
      long_description=long_description,
      long_description_content_type="text/markdown",
      author_email='gomijianxu@gmail.com',
      license='GPLv3',
      packages=find_packages(),
      package_dir={'seispy': 'seispy'},
      package_data={'': ['data/*']},
      install_requires=[
                'obspy>=1.3.0',
                'pandas>=1.0.0',
                'numpy>=1.19.0',
                'scipy>=1.1.0',
                'matplotlib>=3.2.0',
                'pyqt5>=5.12.0',
                # 'pyqtwebengine>=5.12.0'
                # 'folium',
                'scikits.bootstrap>=1.0.0'],
      entry_points={'console_scripts': ['gen_rayp_lib=seispy.psrayp:gen_rayp_lib',
                                        'prf=seispy.scripts:prf',
                                        'srf=seispy.scripts:srf',
                                        'setpar=seispy.rf:setpar',
                                        'rf2depth=seispy.rf2depth_makedata:rf2depth',
                                        'plotrt=seispy.plotRT:main',
                                        'plotr=seispy.plotR:main',
                                        'updatecatalog=seispy.updatecatalog:main',
                                        'ndk2dat=seispy.updatecatalog:ndk2dat',
                                        'ccp_profile=seispy.scripts:ccp_profile',
                                        'hk=seispy.hk:hk',
                                        'pickrf=seispy.pickui:main',
                                        'rfani=seispy.scripts:rfani',
                                        'ccp3d=seispy.scripts:ccp3d',
                                        'rfharmo=seispy.scripts:rfharmo',
                                        'get_pierce_points=seispy.scripts:get_pierce_points',
                                        'veltxt2mod=seispy.modcreator:veltxt2mod']},
      #  include_package_data=True,
      zip_safe=False,
      classifiers=['Programming Language :: Python',
                   'Programming Language :: Python :: 3.7',
                   'Programming Language :: Python :: 3.8',
                   'Programming Language :: Python :: 3.9']
      )
