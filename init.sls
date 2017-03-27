#初始化运行目录
init_dir:
  file:
    - absent
    - name: /tmp/collect_service_ip_port_to_yed/

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
      - file: run_dir

yed_collect_agent:
  cmd.run:
    - name: if test -f /var/local/python2.7.13/bin/python ; then RUNPYTHON=/var/local/python2.7.13/bin/python ; else RUNPYTHON=python ; fi && $RUNPYTHON yed_collect_agent.py -c yed_collect.conf|tee /tmp/collect_service_ip_port_to_yed.log.$(date +%F.%T)
    - cwd: /tmp/collect_service_ip_port_to_yed
    - timeout: 82800
    - user: root
    - require:
      - git: collect2yed_git

rm_files:
  file:
    - absent
    - name: /tmp/collect_service_ip_port_to_yed/
    - require:
      - cmd: yed_collect_agent

