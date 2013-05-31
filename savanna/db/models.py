# Copyright (c) 2013 Mirantis Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sqlalchemy as sa
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import relationship

from savanna.db import model_base as mb
from savanna.utils import crypto
from savanna.utils.openstack.nova import novaclient
from savanna.utils import remote
from savanna.utils.sqlatypes import JsonDictType
from savanna.utils.sqlatypes import JsonListType


CLUSTER_STATUSES = ['Starting', 'Active', 'Stopping', 'Error']


class Cluster(mb.SavannaBase, mb.IdMixin, mb.TenantMixin,
              mb.PluginSpecificMixin, mb.ExtraMixin):
    """Contains all info about cluster."""

    __table_args__ = (
        sa.UniqueConstraint('name', 'tenant_id'),
    )

    name = sa.Column(sa.String(80), nullable=False)
    default_image_id = sa.Column(sa.String(36))
    cluster_configs = sa.Column(JsonDictType())
    node_groups = relationship('NodeGroup', cascade="all,delete",
                               backref='cluster')
    # todo replace String type with sa.Enum(*CLUSTER_STATUSES)
    status = sa.Column(sa.String(80))
    status_description = sa.Column(sa.String(200))
    private_key = sa.Column(sa.Text, default=crypto.generate_private_key())
    base_cluster_template_id = sa.Column(sa.String(36),
                                         sa.ForeignKey('ClusterTemplate.id'))
    base_cluster_template = relationship('ClusterTemplate',
                                         backref="clusters")

    def __init__(self, name, tenant_id, plugin_name, hadoop_version,
                 status=None, status_description=None, default_image_id=None,
                 cluster_configs=None, base_cluster_template_id=None,
                 private_key=None, extra=None):
        self.name = name
        self.tenant_id = tenant_id
        self.plugin_name = plugin_name
        self.hadoop_version = hadoop_version
        self.status = status
        self.status_description = status_description
        self.default_image_id = default_image_id
        self.cluster_configs = cluster_configs or {}
        self.base_cluster_template_id = base_cluster_template_id
        self.private_key = private_key
        self.extra = extra or {}

    def to_dict(self):
        d = super(Cluster, self).to_dict()
        d['node_groups'] = [ng.dict for ng in self.node_groups]
        return d


class NodeGroup(mb.SavannaBase, mb.IdMixin, mb.ExtraMixin):
    """Specifies group of nodes within a cluster."""

    __filter_cols__ = ['cluster_id']
    __table_args__ = (
        sa.UniqueConstraint('name', 'cluster_id'),
    )

    cluster_id = sa.Column(sa.String(36), sa.ForeignKey('Cluster.id'))
    name = sa.Column(sa.String(80), nullable=False)
    flavor_id = sa.Column(sa.String(36), nullable=False)
    image_id = sa.Column(sa.String(36), nullable=False)
    node_processes = sa.Column(JsonListType())
    node_configs = sa.Column(JsonDictType())
    anti_affinity_group = sa.Column(sa.String(36))
    count = sa.Column(sa.Integer, nullable=False)
    instances = relationship('Instance', cascade="all,delete",
                             backref='node_group')
    base_node_group_template_id = sa.Column(sa.String(36),
                                            sa.ForeignKey(
                                                'NodeGroupTemplate.id'))
    base_node_group_template = relationship('NodeGroupTemplate',
                                            backref="node_groups")

    def __init__(self, name, flavor_id, image_id, node_processes, count,
                 node_configs=None, anti_affinity_group=None, extra=None,
                 base_node_group_template_id=None):
        self.name = name
        self.flavor_id = flavor_id
        self.image_id = image_id
        self.node_processes = node_processes
        self.count = count
        self.node_configs = node_configs or {}
        self.anti_affinity_group = anti_affinity_group
        self.extra = extra or {}
        self.base_node_group_template_id = base_node_group_template_id


class Instance(mb.SavannaBase, mb.ExtraMixin):
    """An OpenStack instance created for the cluster."""

    __filter_cols__ = ['node_group_id']
    __table_args__ = (
        sa.UniqueConstraint('instance_id', 'node_group_id'),
    )

    node_group_id = sa.Column(sa.String(36), sa.ForeignKey('NodeGroup.id'))
    instance_id = sa.Column(sa.String(36), primary_key=True)
    instance_name = sa.Column(sa.String(80), nullable=False)
    management_ip = sa.Column(sa.String(15), nullable=False)

    def __init__(self, node_group_id, instance_id, instance_name,
                 management_ip, extra=None):
        self.node_group_id = node_group_id
        self.instance_id = instance_id
        self.instance_name = instance_name
        self.management_ip = management_ip
        self.extra = extra or {}

    @property
    def nova_info(self):
        """Returns info from nova about instance."""
        return novaclient().servers.get(self.instance_id)

    @property
    def username(self):
        ng = self.node_group
        if not hasattr(ng, '_image_username'):
            ng._image_username = novaclient().images.get(ng.image_id).username
        return ng._image_username

    @property
    def hostname(self):
        return self.instance_name

    def remote(self):
        return remote.InstanceInteropHelper(self)


class ClusterTemplate(mb.SavannaBase, mb.IdMixin, mb.TenantMixin,
                      mb.PluginSpecificMixin):
    """Template for Cluster."""

    __table_args__ = (
        sa.UniqueConstraint('name', 'tenant_id'),
    )

    name = sa.Column(sa.String(80), nullable=False)
    description = sa.Column(sa.String(200))
    cluster_configs = sa.Column(JsonDictType())

    # todo add node_groups_suggestion helper

    def __init__(self, name, tenant_id, plugin_name, hadoop_version,
                 cluster_configs=None, description=None):
        self.name = name
        self.tenant_id = tenant_id
        self.plugin_name = plugin_name
        self.hadoop_version = hadoop_version
        self.cluster_configs = cluster_configs or {}
        self.description = description

    def add_node_group_template(self, node_group_template_id, name, count):
        relation = TemplatesRelation(self.id, node_group_template_id, name,
                                     count)
        self.templates_relations.append(relation)
        return relation

    def to_dict(self):
        d = super(ClusterTemplate, self).to_dict()
        d['node_group_templates'] = [tr.dict for tr in
                                     self.templates_relations]
        return d


class NodeGroupTemplate(mb.SavannaBase, mb.IdMixin, mb.TenantMixin,
                        mb.PluginSpecificMixin):
    """Template for NodeGroup."""

    __table_args__ = (
        sa.UniqueConstraint('name', 'tenant_id'),
    )

    name = sa.Column(sa.String(80), nullable=False)
    description = sa.Column(sa.String(200))
    flavor_id = sa.Column(sa.String(36), nullable=False)
    node_processes = sa.Column(JsonListType())
    node_configs = sa.Column(JsonDictType())

    def __init__(self, name, tenant_id, flavor_id, plugin_name,
                 hadoop_version, node_processes, node_configs=None,
                 description=None):
        self.name = name
        self.tenant_id = tenant_id
        self.flavor_id = flavor_id
        self.plugin_name = plugin_name
        self.hadoop_version = hadoop_version
        self.node_processes = node_processes
        self.node_configs = node_configs or {}
        self.description = description


class TemplatesRelation(mb.SavannaBase):
    """NodeGroupTemplate - ClusterTemplate relationship."""

    __filter_cols__ = ['cluster_template_id', 'created', 'updated']

    cluster_template_id = sa.Column(sa.String(36),
                                    sa.ForeignKey('ClusterTemplate.id'),
                                    primary_key=True)
    node_group_template_id = sa.Column(sa.String(36),
                                       sa.ForeignKey('NodeGroupTemplate.id'),
                                       primary_key=True)
    cluster_template = relationship(ClusterTemplate,
                                    backref='templates_relations')
    node_group_template = relationship(NodeGroupTemplate,
                                       backref='templates_relations')
    node_group_name = sa.Column(sa.String(80), nullable=False)
    count = sa.Column(sa.Integer, nullable=False)

    def __init__(self, cluster_template_id, node_group_template_id,
                 node_group_name, count):
        self.cluster_template_id = cluster_template_id
        self.node_group_template_id = node_group_template_id
        self.node_group_name = node_group_name
        self.count = count


ClusterTemplate.node_group_templates = association_proxy("templates_relations",
                                                         "node_group_template")
NodeGroupTemplate.cluster_templates = association_proxy("templates_relations",
                                                        "cluster_template")
