# Centos 6 版本ss 命令 不支持超过7个的匹配，升级到最新版本解决。
ss_for_collect:
  file.managed:
    - name: /var/local/iproute2-4.10.0.tar.gz
    - source: https://www.kernel.org/pub/linux/utils/net/iproute2/iproute2-4.10.0.tar.gz
    - source_hash: md5=a4ea938356c2e1bb5d67c95f5d66de2b
    - mode: 644
  cmd.run:
    - name: tar zxf /var/local/iproute2-4.10.0.tar.gz && cd /var/local/iproute2-4.10.0 && ./configure && make
    - cwd: /var/local
    - require: 
      - file: ss_for_collect
