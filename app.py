#!/usr/bin/env python3
import os
import aws_cdk as cdk

from drupal_fargate.drupal_core_stack import DrupalCoreStack
from drupal_fargate.drupal_fargate_stack import DrupalFargateStack
from drupal_fargate.drupal_waf_stack import DrupalWAFStack

app = cdk.App()
env_cdk = cdk.Environment(account=os.environ["CDK_DEFAULT_ACCOUNT"], region="eu-west-2")

#DB and FileSystem Stack
core_stack = DrupalCoreStack(app, "DrupalCoreStack", env=env_cdk)

#Fargate stack - depends on RDS + EFS
fargate_stack = DrupalFargateStack(app, "DrupalFargateStack", env=env_cdk, core_stack=core_stack)

#WAF Stack
waf_stack = DrupalWAFStack(app, "DrupalWAFStack", env=env_cdk, fargate_stack=fargate_stack, core_stack=core_stack)

app.synth()
