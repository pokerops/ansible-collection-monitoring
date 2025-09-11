# Ansible Collection - pokerops.opensearch

[![Build Status](https://github.com/pokerops/ansible-collection-opensearch/actions/workflows/molecule.yml/badge.svg)](https://github.com/pokerops/ansible-collection-opensearch/actions/wofklows/molecule.yml)
[![Ansible Galaxy](http://img.shields.io/badge/ansible--galaxy-pokerops.opensearch-blue.svg)](https://galaxy.ansible.com/ui/repo/published/pokerops/opensearch/)

An opinionated Helm chart and Ansible collection to install and manage opensearch clusters and clients

## To Do

- Add Molecule test scenario for Kafka backup and restore
- Add Molecule test scenario for Sealed Secrets backup and restore
- Add Grafana operator to base cluster deployment
- Add Grafana deployment to base cluster components
- Add Molecule test scenario for Grafana backup and restore

## Chart variables

## Collection Variables

The following is the list of parameters intended for end-user manipulation:

Cluster wide parameters

| Parameter | Default | Type | Description | Required |
| :-------- | ------: | :--- | :---------- | :------- |

## Collection roles

- pokerops.opensearch.client

## Collection manifests

## Collection playbooks

- pokerops.opensearch.client: Deploy opensearch client

## Testing

You can test the collection directly from sources using command `make test`

Role releases are ci/cd tested against the following distributions:

- Ubuntu Noble
- Ubuntu Jammy

## License

This project is licensed under the terms of the [MIT License](https://opensource.org/license/mit)
