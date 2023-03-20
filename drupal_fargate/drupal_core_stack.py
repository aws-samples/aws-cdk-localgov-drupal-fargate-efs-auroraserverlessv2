from aws_cdk import (
    # Duration,
    Stack,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_rds as rds,
    aws_efs as efs,
    aws_kms as kms,
    aws_s3 as s3,
    aws_iam as iam,
    RemovalPolicy,
    Duration,
    Aspects,
    Tags
)
from constructs import Construct
import cdk_nag

class DrupalCoreStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        #create logging bucket
        self.logging_bucket = s3.Bucket(self, 'drupal_core_logs_bucket',
            enforce_ssl=True,
            versioned=True,
            access_control=s3.BucketAccessControl.LOG_DELIVERY_WRITE,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
        )

        #Create VPC For Drupal
        self.vpc = ec2.Vpc(self, "fargate-vpc", max_azs=3)

        #create custom IAM role for fargate VPC flow logs
        self.vpc_log_role = iam.Role(self, "fargate_role",
            assumed_by=iam.ServicePrincipal("vpc-flow-logs.amazonaws.com")
        )
        #attach permissions
        self.logging_bucket.grant_write(self.vpc_log_role,"fargate-vpc-flowlogs/*")

        #flow logs
        self.vpc_flow_logs = ec2.FlowLog(self, "drupal-flow-log",
            destination=ec2.FlowLogDestination.to_s3(self.logging_bucket,"fargate-vpc-flowlogs/"),
            traffic_type=ec2.FlowLogTrafficType.ALL,
            flow_log_name="fargate-vpc-flowlogs",
            resource_type=ec2.FlowLogResourceType.from_vpc(self.vpc)
        )

        #setup EFS
        self.file_system = efs.FileSystem(
            self, 
            "drupal-efs",
            vpc=self.vpc,
            performance_mode=efs.PerformanceMode.GENERAL_PURPOSE,
            throughput_mode=efs.ThroughputMode.BURSTING,
        )

        #create EFS Access Point
        self.access_point_files = efs.AccessPoint(
            self,
            id="files",
            file_system=self.file_system,
            path="/files",
            posix_user=efs.PosixUser(
                gid="1000",
                uid="1000"
            ),
            create_acl=efs.Acl(
                owner_gid="1000",
                owner_uid="1000",
                permissions="777",
            ),
        )

        #setup EFS volume for ECS
        self.drupal_volume = ecs.Volume(
            name="drupal-files",
            efs_volume_configuration=ecs.EfsVolumeConfiguration(
                file_system_id=self.file_system.file_system_id,
                authorization_config=ecs.AuthorizationConfig(
                    access_point_id=self.access_point_files.access_point_id
                ),
                transit_encryption="ENABLED"
            ),
        )

        self.kms_key = kms.Key(
            self,
            "drupal-key",
            removal_policy=RemovalPolicy.DESTROY,
            enable_key_rotation=True
        )

        #setup new RDS cluster
        self.database = rds.DatabaseCluster(
            self, "RDS-Database",
            default_database_name="drupal",
            deletion_protection=False,
            removal_policy=RemovalPolicy.DESTROY,
            engine=rds.DatabaseClusterEngine.aurora_mysql(
                version=rds.AuroraMysqlEngineVersion.VER_3_02_2,
            ),
            instance_props=rds.InstanceProps(
                vpc=self.vpc,
                instance_type=ec2.InstanceType("serverless"),
                enable_performance_insights=True
            ),
            storage_encrypted=True,
            storage_encryption_key=self.kms_key,
            monitoring_interval=Duration.seconds(5),
            iam_authentication=True,
            port=3333,
            backtrack_window=Duration.minutes(10)
        )
        # get the RDS target group
        self.rds_target_group = self.database.node.find_child('Resource')
        # Override Settings to ensure defaults for Serverless v2
        self.rds_target_group.add_property_override('ServerlessV2ScalingConfiguration',{'MinCapacity': '0.5', 'MaxCapacity': '2'})

        Tags.of(self).add('Application','DrupalFargate')