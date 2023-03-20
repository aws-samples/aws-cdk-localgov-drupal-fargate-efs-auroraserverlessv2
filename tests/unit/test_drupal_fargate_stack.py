import aws_cdk as core
import aws_cdk.assertions as assertions

from drupal_fargate.drupal_fargate_stack import DrupalFargateStack

# example tests. To run these tests, uncomment this file along with the example
# resource in drupal_fargate/drupal_fargate_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = DrupalFargateStack(app, "drupal-fargate")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
