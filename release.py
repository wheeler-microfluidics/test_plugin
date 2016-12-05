import tarfile
import yaml
import subprocess
import re

from microdrop_utility import Version
from path_helpers import path


package_name = 'test_plugin'
plugin_name = 'wheelerlab.test_plugin'

# create a version sting based on the git revision/branch
version = str(Version.from_git_repository())

# write the 'properties.yml' file
properties = {'plugin_name': 'wheelerlab.test_plugin',
              'package_name': package_name, 'version': version}
with open('properties.yml', 'w') as f:
  f.write(yaml.dump(properties))

# create the tar.gz plugin archive
with tarfile.open("%s-%s.tar.gz" % (package_name, version), "w:gz") as tar:
    for name in ['__init__.py', 'properties.yml', 'hooks',
                 'on_plugin_install.py']:
        tar.add(name)
    requirements_file = path(__file__).parent.joinpath('requirements.txt')
    if requirements_file.exists():
        tar.add(requirements_file)
