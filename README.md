Role Name
=========

wcl-zabbix-scripts

Requirements
------------

zabbix-agent should be working before deploying this role to make custom scripts work.

Add the following lines to requirements.yml in your project.

- src: https://github.com/wiredcraft-ops/role-wcl-zabbix-scripts.git
  name: wcl-zabbix-scripts
  version: master

- src: https://github.com/wiredcraft-ops/role-wcl-zabbix-agent.git
  name: wcl-zabbix-agent
  version: master

Role Variables
--------------

None

Dependencies
------------

None

Example Playbook
----------------
Before you use wcl-zabbix-scripts, you need to have zabbix-agent in place,
then include role wcl-zabbix-scripts to the playbook.

    - hosts: all
      sudo: true
      roles:
        - role: wcl-zabbix-agent
          agent_server: "127.0.0.1"
        - role: wcl-zabbix-scripts

License
-------

BSD

Author Information
------------------

An optional section for the role authors to include contact information, or a website (HTML is not allowed).
