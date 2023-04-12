#!/usr/bin/env python3
import os
import aws_cdk as cdk

from drupal_fargate.drupal_core_stack import DrupalCoreStack
from drupal_fargate.drupal_fargate_stack import DrupalFargateStack
from drupal_fargate.drupal_waf_stack import DrupalWAFStack

app = cdk.App()
#env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')),

docker_container = "drupal-9-localgov"

#if you wish to use a custom domain name - enter your domain and zone details
use_zone=False;
domain_name = "localgov.example.com"
zone = "example.com"
zone_id = "YOUR-ZONE-ID"

#DB and FileSystem Stack
core_stack = DrupalCoreStack(
    app, "DrupalCoreStack"+docker_container,
    docker_container=docker_container
)

#Fargate stack - depends on RDS + EFS
fargate_stack = DrupalFargateStack(
    app,
    "DrupalFargateStack"+docker_container,
    core_stack=core_stack,
    docker_container=docker_container
)

#WAF Stack
waf_stack = DrupalWAFStack(app,
    "DrupalWAFStack"+docker_container,
    fargate_stack=fargate_stack,
    core_stack=core_stack,
    docker_container=docker_container,
    use_zone=use_zone,
    domain_name=domain_name,
    zone=zone,
    zone_id=zone_id
)

app.synth()
