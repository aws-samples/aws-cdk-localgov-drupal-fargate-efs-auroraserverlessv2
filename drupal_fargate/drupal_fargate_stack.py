from aws_cdk import (
    # Duration,
    Stack,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_logs as logs,
    Duration,
    Aspects,
    Tags
)
from constructs import Construct
import cdk_nag

class DrupalFargateStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, core_stack, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        #setup default cluster
        self.cluster = ecs.Cluster(self, "fargate-cluster", vpc=core_stack.vpc, container_insights=True)

        #empty task definition for custom container
        self.task_definition = ecs.FargateTaskDefinition(
            self, "TaskDef",
            volumes=[core_stack.drupal_volume],
            memory_limit_mib=2048,
            cpu=1024
        )

        #Create Drupal container task
        self.container_drupal = self.task_definition.add_container(
            "drupal-container",
            image=ecs.ContainerImage.from_asset('./drupal_fargate/container/drupal'),
            logging = ecs.AwsLogDriver(
                stream_prefix = 'drupal-logs',
                log_retention = logs.RetentionDays.ONE_MONTH
            ),
            environment={
                'DRUPAL_DB_HOST': core_stack.database.cluster_endpoint.hostname,
                'DRUPAL_DB_PORT': str(core_stack.database.cluster_endpoint.port),
            },
            secrets={
                'DRUPAL_DB_USER':
                    ecs.Secret.from_secrets_manager(core_stack.database.secret, field="username"),
                'DRUPAL_DB_PASSWORD':
                    ecs.Secret.from_secrets_manager(core_stack.database.secret, field="password"),
                'DRUPAL_DB_NAME':
                    ecs.Secret.from_secrets_manager(core_stack.database.secret, field="dbname"),
            },
        )

        #mount the EFS
        self.drupal_container_volume_mount_point = ecs.MountPoint(
            read_only=False,
            container_path="/var/www/files",
            source_volume=core_stack.drupal_volume.name,
        )
        self.container_drupal.add_mount_points(self.drupal_container_volume_mount_point)
        
        self.port_mapping_drupal = ecs.PortMapping(
            container_port=80,
            host_port=80,
            protocol=ecs.Protocol.TCP
        )
        self.container_drupal.add_port_mappings(self.port_mapping_drupal)

        #create Fargate with ALB
        self.fargate_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self, "FargateService",
            cluster=self.cluster,
            memory_limit_mib=4096,
            cpu=1024,
            task_definition=self.task_definition,
            public_load_balancer=True,
            enable_execute_command=True,
        )
        #allow fargate to talk to EFS / RDS

        self.fargate_service.service.connections.allow_to(core_stack.file_system, ec2.Port.tcp(2049))
        self.fargate_service.service.connections.allow_to(core_stack.database, ec2.Port.tcp(3333))

        #tweak healtch check path (TODO: add 302 as allowed response instead of this)
        self.fargate_service.target_group.configure_health_check(
            path="/robots.txt",
        )
        
        # Setup AutoScaling policy
        self.scaling = self.fargate_service.service.auto_scale_task_count(
            min_capacity=2,
            max_capacity=4
        )
        self.scaling.scale_on_cpu_utilization(
            "CpuScaling",
            target_utilization_percent=50,
            scale_in_cooldown=Duration.seconds(60),
            scale_out_cooldown=Duration.seconds(60),
        )

        Tags.of(self).add('Application','DrupalFargate')