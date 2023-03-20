#!/usr/bin/env python3
import os
import aws_cdk as cdk

from drupal_fargate.drupal_core_stack import DrupalCoreStack
from drupal_fargate.drupal_fargate_stack import DrupalFargateStack
from drupal_fargate.drupal_waf_stack import DrupalWAFStack

app = cdk.App()
#env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')),

#DB and FileSystem Stack
core_stack = DrupalCoreStack(app, "DrupalCoreStack")

#Fargate stack - depends on RDS + EFS
fargate_stack = DrupalFargateStack(app, "DrupalFargateStack", core_stack=core_stack)

#WAF Stack
waf_stack = DrupalWAFStack(app, "DrupalWAFStack", fargate_stack=fargate_stack, core_stack=core_stack)

app.synth()
