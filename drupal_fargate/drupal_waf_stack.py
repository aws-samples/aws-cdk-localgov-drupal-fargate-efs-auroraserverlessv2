from aws_cdk import (
    # Duration,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_iam as iam,
    Stack,
    Aspects,
    CfnOutput,
    Tags
)
from constructs import Construct
from aws_solutions_constructs.aws_wafwebacl_cloudfront import WafwebaclToCloudFront
import cdk_nag

class DrupalWAFStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, fargate_stack, core_stack, docker_container, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        #Add Cloudfront to front of ALB, with HTTPS
        #Connect to ALB with HTTP only (no https on ALB)
        self.cloudfront_distro = cloudfront.Distribution(
            self,
            "drupal-fargate-dist-v2",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.LoadBalancerV2Origin(
                    fargate_stack.fargate_service.load_balancer,
                    protocol_policy=cloudfront.OriginProtocolPolicy.HTTP_ONLY,
                )
            ),
            enable_logging=True,
            log_bucket=core_stack.logging_bucket,
            log_file_prefix="cloudfront-logs",
            minimum_protocol_version=cloudfront.SecurityPolicyProtocol.TLS_V1_2_2021,            
        )
        #create custom IAM role for fargate VPC flow logs
        self.cf_log_role = iam.Role(self, "fargate_cf_role",
            assumed_by=iam.ServicePrincipal("cloudfront.amazonaws.com")
        )
        #attach permissions
        core_stack.logging_bucket.grant_write(self.cf_log_role,"cloudfront-logs/*")

        #import WAF for Cloudfront Construct
        # This construct can only be attached to a configured CloudFront.
        # Only runs in us-east-1 as has scope "CLOUDFRONT"
        #self.waf_for_cloudfront = WafwebaclToCloudFront(self, 'waf_web_acl_us',
        #    existing_cloud_front_web_distribution = self.cloudfront_distro
        #)
        
        CfnOutput(self, 'CloudfrontDistribution', value="https://"+self.cloudfront_distro.domain_name)
        CfnOutput(self, 'CloudfrontDistributionInstallPath', value="https://"+self.cloudfront_distro.domain_name+"/core/install.php")

        Tags.of(self).add('Application','DrupalFargate')