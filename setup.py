# -*- coding: utf-8 -*-

import os
import sys
from setuptools import setup, find_namespace_packages
from setuptools.command.develop import develop
from setuptools.command.install import install

with open('README.md', 'r') as file:
    long_description = file.read()

with open(os.path.join('.', 'qudi', 'core', 'VERSION'), 'r') as file:
    version = file.read().strip()

unix_dep = ['wheel',
            'cycler',
            'entrypoints',
            'fysom',
            'GitPython',
            'jupyter',
            'jupytext',
            'lmfit',
            'matplotlib',
            'numpy',
            'pyqtgraph',
            'PySide2',
            'rpyc',
            'ruamel.yaml',
            'scipy',
            ]

windows_dep = ['wheel',
               'cycler',
               'entrypoints',
               'fysom',
               'GitPython',
               'jupyter',
               'jupytext',
               'lmfit',
               'matplotlib',
               'numpy',
               'pyqtgraph',
               'PySide2',
               'rpyc',
               'ruamel.yaml',
               'scipy',
               ]


class PrePostDevelopCommands(develop):
    """ Pre- and Post-installation script for development mode.
    """

    def run(self):
        # PUT YOUR PRE-INSTALL SCRIPT HERE or CALL A FUNCTION
        develop.run(self)
        # PUT YOUR POST-INSTALL SCRIPT HERE or CALL A FUNCTION
        try:
            from qudi.core.qudikernel import install_kernel
            install_kernel()
        except:
            pass


class PrePostInstallCommands(install):
    """ Pre- and Post-installation for installation mode.
    """

    def run(self):
        # PUT YOUR PRE-INSTALL SCRIPT HERE or CALL A FUNCTION
        install.run(self)
        # PUT YOUR POST-INSTALL SCRIPT HERE or CALL A FUNCTION
        try:
            from qudi.core.qudikernel import install_kernel
            install_kernel()
        except:
            pass

packages = ['qudi']
packages.extend(f'qudi.{pkg}' for pkg in find_namespace_packages(where='qudi'))

setup(name='qudi-core',
      version=version,
      packages=packages,
      # packages=['qudi',
      #           'qudi.core',
      #           'qudi.core.gui',
      #           'qudi.core.gui.main_gui',
      #           'qudi.core.logger',
      #           'qudi.core.scripting',
      #           'qudi.util',
      #           'qudi.util.fit_models',
      #           'qudi.util.widgets',
      #           'qudi.tools',
      #           'qudi.tools.config_editor'
      #           ],
      package_data={'': ['LICENSE', 'LICENSE.LESSER', 'AUTHORS.md', 'README.md'],
                    'qudi': ['artwork/logo/*',
                             'artwork/icons/oxygen/*',
                             'artwork/icons/oxygen/**/*.png',
                             'artwork/icons/qudiTheme/*',
                             'artwork/icons/qudiTheme/**/*.png',
                             'artwork/logo/*.png',
                             'artwork/logo/*.ico',
                             'artwork/logo/*.txt',
                             'artwork/styles/*.qss',
                             'artwork/styles/*.txt',
                             'artwork/styles/**/*.png',
                             'artwork/styles/**/*.txt',
                             ],
                    'qudi.core': ['VERSION', 'default.cfg']
                    },
      description='A modular measurement application framework',
      long_description=long_description,
      long_description_content_type='text/markdown',
      url='https://github.com/Ulm-IQO/qudi-core',
      keywords=['diamond',
                'quantum',
                'confocal',
                'experiment',
                'measurement',
                'framework',
                'lab',
                'laboratory',
                'instrumentation',
                'instrument',
                'modular'
                ],
      license='LGPLv3',
      install_requires=windows_dep if sys.platform == 'win32' else unix_dep,
      python_requires='~=3.8',
      cmdclass={'develop': PrePostDevelopCommands, 'install': PrePostInstallCommands},
      entry_points={
          'console_scripts': ['qudi=qudi.runnable:main',
                              'qudi-config-editor=qudi.tools.config_editor.config_editor:main',
                              'qudi-uninstall-kernel=qudi.core.qudikernel:uninstall_kernel',
                              'qudi-install-kernel=qudi.core.qudikernel:install_kernel'
                              ]
      },
      zip_safe=False
      )
