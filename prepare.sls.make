python_require_common_package:
  pkg.installed:
    - pkgs:
      - git
      - gcc
      - zlib
      - zlib-devel
      - openssl-devel
      #- mysql
      #- mysql-devel

python_for_collect:
  file.managed:
    - name: /tmp/Python-2.7.13.tar.xz
    - source: salt://collect2yed/files/Python-2.7.13.tar.xz
    - mode: 644
  cmd.run:
    - name: tar xf /tmp/Python-2.7.13.tar.xz && cd /tmp/Python-2.7.13 && ./configure --prefix=/var/local/python2.7.13 --quiet && make -s && make -s install 
    - cwd: /tmp
    - require: 
      - file: python_for_collect
      - pkg: python_require_common_package
#    - onchanges:
#      - file: python_for_collect

ez_setup_install:
  file.managed:
    - name: /var/local/python2.7.13/bin/ez_setup.py
    - sources:
      - salt://collect2yed/files/ez_setup.py
  cmd.run:
    - name: /var/local/python2.7.13/bin/python ez_setup.py
    - cwd: /var/local/python2.7.13/bin/
    - require:
      - cmd: python_for_collect
      - file: ez_setup_eggfile

ez_setup_eggfile:
  file.managed:
    - name: /var/local/python2.7.13/bin/setuptools-0.6c11-py2.7.egg
    - sources:
      - salt://collect2yed/files/setuptools-0.6c11-py2.7.egg

pip_install:
  file.managed:
    - name: /var/local/python2.7.13/bin/get-pip.py
    - source: salt://collect2yed/files/get-pip.py
  cmd.run:
    - name: set -x ; trycount=5;while test $trycount -gt 0;do /var/local/python2.7.13/bin/python get-pip.py ;if test $? -ne 0;then trycount=$(($trycount-1));else break ;fi;done ;set +x
    - cwd: /var/local/python2.7.13/bin/
    - require:
      - cmd: python_for_collect

#python_pip_require:
#  cmd.run:
#    - name: /var/local/python2.7.13/bin/pip install MySQL-python netifaces psutil
#    - cwd: /var/local/python2.7.13/bin/
#    - user: root
#    - require:
#      - cmd: pip_install
#      - cmd: ez_setup_install

python_pip_require:
  pip.installed:
    - requirements: salt://collect2yed/REQUIREMENTS.txt
#    - names:
#      - MySQL-python
#      - netifaces
#      - psutil
    - cwd: /var/local/python2.7.13/bin/
    - bin_env: /var/local/python2.7.13/bin/pip
#    - pip_bin: /var/local/python2.7.13/bin/pip
    - user: root
    - require:
      - cmd: pip_install
      - cmd: ez_setup_install
