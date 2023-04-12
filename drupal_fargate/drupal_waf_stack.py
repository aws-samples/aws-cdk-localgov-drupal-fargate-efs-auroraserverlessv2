from aws_cdk import (
    # Duration,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_iam as iam,
    aws_route53 as r53,
    aws_route53_targets as r53t,
    aws_certificatemanager as acm,
    Stack,
    Aspects,
    CfnOutput,
    Tags
)
from constructs import Construct
from aws_solutions_constructs.aws_wafwebacl_cloudfront import WafwebaclToCloudFront
import cdk_nag

class DrupalWAFStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, fargate_stack, core_stack, docker_container, use_zone, domain_name, zone, zone_id, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        if use_zone == True:
            #custom domain name and certificate
            self.zone = r53.HostedZone.from_hosted_zone_attributes(
                self,
                "drupal-zone",
                zone_name=zone,
                hosted_zone_id=zone_id,
            )

            self.drupal_cert = acm.DnsValidatedCertificate(self, "drupal-cert2",
                hosted_zone=self.zone,
                region="us-east-1",
                domain_name=domain_name,
                validation=acm.CertificateValidation.from_dns(self.zone)
            )

            #Add Cloudfront to front of ALB, with HTTPS
            #Connect to ALB with HTTP only (no https on ALB)
            self.cloudfront_distro = cloudfront.Distribution(
                self,
                "drupal-fargate-dist-v2",
                default_behavior=cloudfront.BehaviorOptions(
                    origin=origins.LoadBalancerV2Origin(
                        fargate_stack.fargate_service.load_balancer,
                        protocol_policy=cloudfront.OriginProtocolPolicy.HTTP_ONLY,
                        custom_headers={"x-cloudfront-custom-security":"localgovdrupal"}
                    ),
                    allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
                    cache_policy=cloudfront.CachePolicy(
                        self,
                        "localgov_cache_policy",
                        header_behavior=cloudfront.CacheHeaderBehavior.allow_list("Origin","CloudFront-Forwarded-Proto","Host"),
                        cookie_behavior=cloudfront.CacheCookieBehavior.all(),
                        query_string_behavior=cloudfront.CacheQueryStringBehavior.all(),
                        enable_accept_encoding_gzip=True,
                    )
                ),
                price_class=cloudfront.PriceClass.PRICE_CLASS_100,
                domain_names=[domain_name],
                certificate=self.drupal_cert,
                enable_logging=True,
                log_bucket=core_stack.logging_bucket,
                log_file_prefix="cloudfront-logs",
                minimum_protocol_version=cloudfront.SecurityPolicyProtocol.TLS_V1_2_2021,
            )

            self.arecord = r53.CnameRecord(self, "drupal_alias",
                zone=self.zone,
                domain_name=self.cloudfront_distro.distribution_domain_name,
                record_name=domain_name,
                delete_existing=True
            )
        else:
            #Add Cloudfront to front of ALB, with HTTPS
            #Connect to ALB with HTTP only (no https on ALB)
            self.cloudfront_distro = cloudfront.Distribution(
                self,
                "drupal-fargate-dist-v2",
                default_behavior=cloudfront.BehaviorOptions(
                    origin=origins.LoadBalancerV2Origin(
                        fargate_stack.fargate_service.load_balancer,
                        protocol_policy=cloudfront.OriginProtocolPolicy.HTTP_ONLY,
                        custom_headers={"x-cloudfront-custom-security":"localgovdrupal"}
                    ),
                    allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
                    cache_policy=cloudfront.CachePolicy(
                        self,
                        "localgov_cache_policy",
                        header_behavior=cloudfront.CacheHeaderBehavior.allow_list("Origin","CloudFront-Forwarded-Proto","Host"),
                        cookie_behavior=cloudfront.CacheCookieBehavior.all(),
                        query_string_behavior=cloudfront.CacheQueryStringBehavior.all(),
                        enable_accept_encoding_gzip=True,
                    )
                ),
                price_class=cloudfront.PriceClass.PRICE_CLASS_100,
                enable_logging=True,
                log_bucket=core_stack.logging_bucket,
                log_file_prefix="cloudfront-logs",
                minimum_protocol_version=cloudfront.SecurityPolicyProtocol.TLS_V1_2_2021,
            )
            domain_name = self.cloudfront_distro.domain_name

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
        CfnOutput(self, 'CloudfrontCustomDistributionInstallPath', value="https://"+domain_name+"/core/install.php")

        Tags.of(self).add('Application','DrupalFargate')