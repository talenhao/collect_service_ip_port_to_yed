init_dir:
  file:
    - absent
    - name: /tmp/collect_service_ip_port_to_yed/

python_require_common_package: # id
  pkg.installed: # state.funcation
    - pkgs:
      - python-pip
      - python-devel
      - python-netifaces
      - git
      - MySQL-python
#  pip.installed:
#    - pkgs:
#      - MySQL-python
#      - netifaces

run_dir:
  file.directory:
    - name: /tmp/collect_service_ip_port_to_yed/
    - user: root
    - group: root
    - dir_mode: 755
    - file_mode: 644
    - recurse:
      - user
      - group
      - mode
      - ignore_dirs
    - require:
      - file: init_dir

collect2yed_git:
  git.latest:
    - name: https://github.com/talenhao/collect_service_ip_port_to_yed.git
    - target: /tmp/collect_service_ip_port_to_yed/
    - force_reset: True
    - require:
      - pkg: python_require_common_package
      - file: run_dir

yed_collect_agent:
  cmd.run:
    - name: python yed_collect_agent.py -c yed_collect.conf|tee /tmp/collect_service_ip_port_to_yed.log.$(date +%F.%T)
    - cwd: /tmp/collect_service_ip_port_to_yed
    - timeout: 82800
    - require:
      - git: collect2yed_git

rm_files:
  file:
    - absent
    - name: /tmp/collect_service_ip_port_to_yed/
    - require:
      - cmd: yed_collect_agent

