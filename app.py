#!/usr/bin/env python3
import os
import aws_cdk as cdk

from drupal_fargate.drupal_core_stack import DrupalCoreStack
from drupal_fargate.drupal_fargate_stack import DrupalFargateStack
from drupal_fargate.drupal_waf_stack import DrupalWAFStack

app = cdk.App()
#env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')),

docker_contatiner = "drupal-9-localgov"

#DB and FileSystem Stack
core_stack = DrupalCoreStack(app, "DrupalCoreStack"+docker_contatiner, docker_container=docker_contatiner)

#Fargate stack - depends on RDS + EFS
fargate_stack = DrupalFargateStack(app, "DrupalFargateStack"+docker_contatiner, core_stack=core_stack, docker_container=docker_contatiner)

#WAF Stack
waf_stack = DrupalWAFStack(app, "DrupalWAFStack"+docker_contatiner, fargate_stack=fargate_stack, core_stack=core_stack, docker_container=docker_contatiner)

app.synth()
