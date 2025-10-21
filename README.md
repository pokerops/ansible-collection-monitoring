# Ansible Collection - pokerops.monitoring

[![Build Status](https://github.com/pokerops/ansible-collection-monitoring/actions/workflows/build.yml/badge.svg)](https://github.com/pokerops/ansible-collection-monitoring/actions/workflows/build.yml)
[![Ansible Galaxy](http://img.shields.io/badge/ansible--galaxy-pokerops.monitoring-blue.svg)](https://galaxy.ansible.com/ui/repo/published/pokerops/monitoring/)

An Ansible collection to deploy and manage monitoring infrastructure using Elastic Beats (Filebeat, Metricbeat, Heartbeat, Packetbeat) and Vector for log/metric collection and forwarding.

## Description

This collection provides roles and playbooks for setting up comprehensive monitoring and observability infrastructure. It includes support for:

- [**Filebeat**](https://www.elastic.co/beats/filebeat): Lightweight shipper for forwarding and centralizing log data
- [**Metricbeat**](https://www.elastic.co/beats/metricbeat): Lightweight shipper for metrics collection
- [**Heartbeat**](https://www.elastic.co/beats/heartbeat): Uptime monitoring for services
- [**Vector**](https://vector.dev/): High-performance observability data pipeline

## Modes of operation

The collection supports two primary modes of operation for deploying monitoring agents:

- Legacy Mode: Direct installation of Elastic Beats on target hosts for log and metric collection forwarding to local Vector instance that relays to upstream Elasticsearch and Logstash deployments
- Standard Mode: Standard metric collection using Vector OS source with sink to server side Vector and ELK/Grafana stack managed by Helm chart

## ToDo

- Move Vector tasks to standalone role
- Add playbook for server side deployment
- (Optional) Add Helm chart for deployment of server side components

## Installation

### From Ansible Galaxy

```bash
ansible-galaxy collection install pokerops.monitoring
```

### From Source

```bash
git clone https://github.com/pokerops/ansible-collection-monitoring.git
cd ansible-collection-monitoring
devbox run make install
```

## Playbooks

The collection provides the following playbooks for common operations:

- `playbooks/install.yml`: Agent install playbook
- `playbooks/uninstall.yml`: Agent uninstallation playbook

## Usage Examples

### Basic Filebeat Installation

```yaml
---
- name: Deploy Filebeat
  hosts: servers
  become: true
  vars:
    filebeat_package_state: latest
    filebeat_conf_manage: true
    filebeat_conf:
      fields:
        environment: production
      filebeat.inputs:
        - type: log
          enabled: true
          paths:
            - /var/log/syslog
            - /var/log/auth.log
      output.elasticsearch:
        hosts: ["https://elasticsearch.example.com:9200"]
        username: "elastic"
        password: "changeme"
      setup.kibana:
        host: "https://kibana.example.com:5601"
  roles:
    - pokerops.monitoring.filebeat
```

### Metricbeat with Auto-detection

```yaml
---
- name: Deploy Metricbeat
  hosts: servers
  become: true
  vars:
    metricbeat_package_state: present
    metricbeat_conf_manage: true
    metricbeat_conf_docker_hosts:
      - unix:///var/run/docker.sock
    metricbeat_conf_postgresql_hosts:
      - postgres://localhost:5432
    metricbeat_conf_postgresql_user: monitoring
    metricbeat_conf_postgresql_pass: "{{ vault_postgres_password }}"
  roles:
    - pokerops.monitoring.metricbeat
```

### Heartbeat for Service Monitoring

```yaml
---
- name: Deploy Heartbeat
  hosts: monitoring_servers
  become: true
  vars:
    heartbeat_conf:
      heartbeat.monitors:
        - type: http
          schedule: "@every 60s"
          urls: ["https://example.com"]
          check.response.status: 200
        - type: icmp
          schedule: "@every 5s"
          hosts: ["192.168.1.1"]
      output.elasticsearch:
        hosts: ["https://elasticsearch.example.com:9200"]
  roles:
    - pokerops.monitoring.heartbeat
```

## Role Variables

Each role has extensive configuration options. Please refer to the `defaults/main.yml` file in each role directory for detailed variable documentation:

- [filebeat defaults](roles/filebeat/defaults/main.yml)
- [metricbeat defaults](roles/metricbeat/defaults/main.yml)
- [heartbeat defaults](roles/heartbeat/defaults/main.yml)
- [packetbeat defaults](roles/packetbeat/defaults/main.yml)

## Testing

This collection uses Molecule for testing. To run tests:

```bash
devbox shell
make install
make test
```

### Tested Distributions

Roles are tested against:

- Ubuntu Noble (24.04)
- Ubuntu Jammy (22.04)
- Ubuntu Bionic (20.04)
- Debian Bookworm
- Debian Bullseye

## Development

This collection is developed using [Devbox](https://devbox.sh) for a consistent development environment.
Default build and test dependencies and tasks are managed with [ansible-utils plugin ](https://github.com/pokerops/ansible-utilspokerops/ansible-utils.git)

To set up a local development environment:

```bash
devbox shell
devbox make install
devbox make create prepare converge verify
```

The collection structure is as follows after import of external roles:

```
pokerops.monitoring/
├── galaxy.yml              # Collection metadata
├── requirements.yml        # Collection dependencies
├── roles/                  # Ansible roles
│   ├── defaults/          # Shared defaults
│   ├── elastic_repo/      # Elastic repository setup
│   ├── filebeat/          # Filebeat role
│   ├── heartbeat/         # Heartbeat role
│   ├── metricbeat/        # Metricbeat role
│   └── packetbeat/        # Packetbeat role
├── playbooks/             # Ready-to-use playbooks
│   ├── beats/            # Beat-specific playbooks
│   ├── vector/           # Vector playbooks
│   ├── check.yml         # Status checks
│   ├── install.yml       # Main installation
│   └── uninstall.yml     # Main removal
└── extensions/           # Molecule scenarios
    └── molecule/
        ├── common/       # Shared test files
        └── default/      # Default test scenario
```

## License

This project is licensed under the terms of the [MIT License](https://opensource.org/license/mit).

## Author

Ted Cook <358176+teddyphreak@users.noreply.github.com>

## Support

- **Issues**: [GitHub Issues](https://github.com/pokerops/ansible-collection-monitoring/issues)
- **Repository**: [GitHub](https://github.com/pokerops/ansible-collection-monitoring)
- **Documentation**: [GitHub Docs](https://github.com/pokerops/ansible-collection-monitoring)

## Acknowledgments

This collection builds upon and includes modified versions of roles from the nephelaiio namespace, adapted for the pokerops infrastructure requirements.
