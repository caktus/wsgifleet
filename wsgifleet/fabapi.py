import os
import urllib2

import boto.ec2
import boto.cloudformation
import boto.exception

from fabric.decorators import runs_once
from fabric.api import env, run, cd, settings, sudo, abort
from fabric.contrib.project import rsync_project


def _connect_ec2():
    return boto.ec2.connect_to_region(
            region_name=os.environ['AWS_EC2_REGION'],
            aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'], 
            aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'])


def _connect_cloudformation():
    return boto.cloudformation.connect_to_region(
            region_name=os.environ['AWS_EC2_REGION'],
            aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'], 
            aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'])


def _ec2_public_dns(tags):
    public_dns = []
    conn = _connect_ec2()
    filters = dict(('tag:%s' % k, v) for k, v in tags.items())
    print filters
    reservations = conn.get_all_instances(filters=filters)
    for reservation in reservations:
        for instance in reservation.instances:
            public_dns.append(str(instance.public_dns_name))
    return public_dns


def _ec2_tags(**kwargs):
    if not kwargs:
        abort('Must specify at least one tag (key/value pair)')
    return kwargs


def ec2(**kwargs):
    env.hosts = _ec2_public_dns(_ec2_tags(**kwargs))
    print env.hosts


def ec2_new(**kwargs):
    count = kwargs.pop('count')
    type_ = kwargs.pop('type')
    conn = _connect_cloudformation()
    stack_name = '-'.join([kwargs['app'], kwargs['env']])
    conn.create_stack(
        stack_name=stack_name,
        template_url='https://s3.amazonaws.com/coreos.com/dist/aws/coreos-stable-pv.template',
        tags=_ec2_tags(**kwargs),
        parameters=[
            ('AdvertisedIPAddress', 'private'),
            ('AllowSSHFrom', '0.0.0.0/0'),
            ('ClusterSize', '3'),
            ('DiscoveryURL', urllib2.urlopen('https://discovery.etcd.io/new').read()),
            ('InstanceType', type_),
            ('KeyPair', os.environ['AWS_EC2_KEY_PAIR'])])
    print 'Hosts for stack %s should be starting.' % stack_name


@runs_once
def destroy_all():
    run("fleetctl list-units|grep .service|cut -d$'\t' -f1 | xargs fleetctl destroy", shell=True)


@runs_once
def submit_all():
    rsync_project('/home/core', os.path.join(os.path.dirname(__file__), 'systemd'), exclude=['fabfile.py', '*.pyc'], delete=True)
    with cd('systemd'):
        run('fleetctl submit *.service')

