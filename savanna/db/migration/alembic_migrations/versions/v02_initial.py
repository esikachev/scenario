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

"""v02_initial

Revision ID: 177f06c249e5
Revises: None
Create Date: 2013-06-22 18:16:30.002766

"""

# revision identifiers, used by Alembic.
revision = '177f06c249e5'
down_revision = None

from alembic import op
import sqlalchemy as sa

from savanna.utils import sqlatypes as st

sa.JSONEncoded = st.JSONEncoded


def upgrade():
    op.create_table('ClusterTemplate',
                    sa.Column('created', sa.DateTime(), nullable=False),
                    sa.Column('updated', sa.DateTime(), nullable=False),
                    sa.Column('id', sa.String(length=36), nullable=False),
                    sa.Column('tenant_id', sa.String(length=36),
                              nullable=True),
                    sa.Column('plugin_name', sa.String(length=80),
                              nullable=False),
                    sa.Column('hadoop_version', sa.String(length=80),
                              nullable=False),
                    sa.Column('name', sa.String(length=80), nullable=False),
                    sa.Column('description', sa.String(length=200),
                              nullable=True),
                    sa.Column('cluster_configs', sa.JSONEncoded(),
                              nullable=True),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('name', 'tenant_id'))

    op.create_table('NodeGroupTemplate',
                    sa.Column('created', sa.DateTime(), nullable=False),
                    sa.Column('updated', sa.DateTime(), nullable=False),
                    sa.Column('id', sa.String(length=36), nullable=False),
                    sa.Column('tenant_id', sa.String(length=36),
                              nullable=True),
                    sa.Column('plugin_name', sa.String(length=80),
                              nullable=False),
                    sa.Column('hadoop_version', sa.String(length=80),
                              nullable=False),
                    sa.Column('name', sa.String(length=80), nullable=False),
                    sa.Column('description', sa.String(length=200),
                              nullable=True),
                    sa.Column('flavor_id', sa.String(length=36),
                              nullable=False),
                    sa.Column('node_processes', sa.JSONEncoded(),
                              nullable=True),
                    sa.Column('node_configs', sa.JSONEncoded(), nullable=True),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('name', 'tenant_id'))

    op.create_table('Cluster',
                    sa.Column('created', sa.DateTime(), nullable=False),
                    sa.Column('updated', sa.DateTime(), nullable=False),
                    sa.Column('id', sa.String(length=36), nullable=False),
                    sa.Column('tenant_id', sa.String(length=36),
                              nullable=True),
                    sa.Column('plugin_name', sa.String(length=80),
                              nullable=False),
                    sa.Column('hadoop_version', sa.String(length=80),
                              nullable=False),
                    sa.Column('extra', sa.JSONEncoded(), nullable=True),
                    sa.Column('name', sa.String(length=80), nullable=False),
                    sa.Column('default_image_id', sa.String(length=36),
                              nullable=True),
                    sa.Column('cluster_configs', sa.JSONEncoded(),
                              nullable=True),
                    sa.Column('status', sa.String(length=80), nullable=True),
                    sa.Column('status_description', sa.String(length=200),
                              nullable=True),
                    sa.Column('private_key', sa.Text(), nullable=True),
                    sa.Column('user_keypair_id', sa.String(length=80),
                              nullable=True),
                    sa.Column('cluster_template_id', sa.String(length=36),
                              nullable=True),
                    sa.ForeignKeyConstraint(['cluster_template_id'],
                                            ['ClusterTemplate.id'], ),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('name', 'tenant_id'))

    op.create_table('TemplatesRelation',
                    sa.Column('created', sa.DateTime(), nullable=False),
                    sa.Column('updated', sa.DateTime(), nullable=False),
                    sa.Column('id', sa.String(length=36), nullable=False),
                    sa.Column('cluster_template_id', sa.String(length=36),
                              nullable=True),
                    sa.Column('node_group_template_id', sa.String(length=36),
                              nullable=True),
                    sa.Column('name', sa.String(length=80), nullable=False),
                    sa.Column('flavor_id', sa.String(length=36),
                              nullable=True),
                    sa.Column('node_processes', sa.JSONEncoded(),
                              nullable=True),
                    sa.Column('node_configs', sa.JSONEncoded(), nullable=True),
                    sa.Column('count', sa.Integer(), nullable=True),
                    sa.ForeignKeyConstraint(['cluster_template_id'],
                                            ['ClusterTemplate.id'], ),
                    sa.ForeignKeyConstraint(['node_group_template_id'],
                                            ['NodeGroupTemplate.id'], ),
                    sa.PrimaryKeyConstraint('id'))

    op.create_table('NodeGroup',
                    sa.Column('created', sa.DateTime(), nullable=False),
                    sa.Column('updated', sa.DateTime(), nullable=False),
                    sa.Column('id', sa.String(length=36), nullable=False),
                    sa.Column('extra', sa.JSONEncoded(), nullable=True),
                    sa.Column('cluster_id', sa.String(length=36),
                              nullable=True),
                    sa.Column('name', sa.String(length=80), nullable=False),
                    sa.Column('flavor_id', sa.String(length=36),
                              nullable=False),
                    sa.Column('image_id', sa.String(length=36), nullable=True),
                    sa.Column('node_processes', sa.JSONEncoded(),
                              nullable=True),
                    sa.Column('node_configs', sa.JSONEncoded(), nullable=True),
                    sa.Column('anti_affinity_group', sa.String(length=36),
                              nullable=True),
                    sa.Column('count', sa.Integer(), nullable=False),
                    sa.Column('volumes_per_node', sa.Integer(), nullable=True),
                    sa.Column('volumes_size', sa.Integer(), nullable=True),
                    sa.Column('volume_mount_prefix', sa.String(length=80),
                              nullable=True),
                    sa.Column('node_group_template_id', sa.String(length=36),
                              nullable=True),
                    sa.ForeignKeyConstraint(['cluster_id'], ['Cluster.id'], ),
                    sa.ForeignKeyConstraint(['node_group_template_id'],
                                            ['NodeGroupTemplate.id'], ),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('name', 'cluster_id'))

    op.create_table('Instance',
                    sa.Column('created', sa.DateTime(), nullable=False),
                    sa.Column('updated', sa.DateTime(), nullable=False),
                    sa.Column('extra', sa.JSONEncoded(), nullable=True),
                    sa.Column('node_group_id', sa.String(length=36),
                              nullable=True),
                    sa.Column('instance_id', sa.String(length=36),
                              nullable=False),
                    sa.Column('instance_name', sa.String(length=80),
                              nullable=False),
                    sa.Column('internal_ip', sa.String(length=15),
                              nullable=True),
                    sa.Column('management_ip', sa.String(length=15),
                              nullable=True),
                    sa.Column('volumes', sa.JSONEncoded(), nullable=True),
                    sa.ForeignKeyConstraint(['node_group_id'],
                                            ['NodeGroup.id'], ),
                    sa.PrimaryKeyConstraint('instance_id'),
                    sa.UniqueConstraint('instance_id', 'node_group_id'))


def downgrade():
    op.drop_table('Instance')
    op.drop_table('NodeGroup')
    op.drop_table('TemplatesRelation')
    op.drop_table('Cluster')
    op.drop_table('NodeGroupTemplate')
    op.drop_table('ClusterTemplate')
