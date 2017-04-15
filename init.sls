#初始化运行目录
upload_files:
  file.recurse:
    - name: /tmp/collect_service_ip_port_to_yed
    - source: salt://collect2yed/files/collect_service_ip_port_to_yed

# 执行脚本
yed_collect_agent:
  cmd.run:
    - name: if test -f /var/local/python2.7.13/bin/python ; then RUNPYTHON=/var/local/python2.7.13/bin/python ; else RUNPYTHON=python ; fi && $RUNPYTHON yed_collect_agent.py -c yed_collect.conf
    #|tee /tmp/collect_service_ip_port_to_yed.log.$(date +%F.%T)
    - cwd: /tmp/collect_service_ip_port_to_yed
    - timeout: 82800
    - user: root
    - require:
      - file: upload_files

# 删除运行目录
rm_files:
  file:
    - absent
    - name: /tmp/collect_service_ip_port_to_yed/
    - require:
      - cmd: yed_collect_agent

