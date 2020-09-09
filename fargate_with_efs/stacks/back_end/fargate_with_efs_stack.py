from aws_cdk import aws_ec2 as _ec2
from aws_cdk import aws_ecs as _ecs
from aws_cdk import aws_ecs_patterns as _ecs_patterns
from aws_cdk import aws_logs as _logs
from aws_cdk import core


class GlobalArgs:
    """
    Helper to define global statics
    """

    OWNER = "MystiqueAutomation"
    ENVIRONMENT = "production"
    REPO_NAME = "fargate-with-efs"
    SOURCE_INFO = f"https://github.com/miztiik/{REPO_NAME}"
    VERSION = "2020_09_07"
    MIZTIIK_SUPPORT_EMAIL = ["mystique@example.com", ]


class FargateWithEfsStack(core.Stack):

    def __init__(
            self,
            scope: core.Construct,
            id: str,
            custom_vpc,
            efs_share,
            efs_ap_nginx,
            enable_container_insights: bool = False,
            ** kwargs
    ) -> None:
        super().__init__(scope, id, **kwargs)

        # Create Security Group to allow Fargate Cluster instances to access EFS.
        web_svc_sg = _ec2.SecurityGroup(
            self,
            id="webSvcSecurityGroup",
            vpc=custom_vpc,
            security_group_name=f"web_svc_sg_{id}",
            description="Security Group to allow Fargate Cluster instances to access EFS"
        )

        # Allow Internet access to Fargate web service
        web_svc_sg.add_ingress_rule(
            _ec2.Peer.any_ipv4(),
            _ec2.Port.tcp(80),
            description="Allow Internet access to web service"
        )

        # The code that defines your stack goes here
        fargate_cluster = _ecs.Cluster(
            self,
            "fargateClusterId",
            cluster_name=f"web-app-{id}",
            # container_insights=enable_container_insights,
            vpc=custom_vpc
        )

        web_app_task_def = _ecs.FargateTaskDefinition(
            self,
            "webAppTaskDef",
            cpu=256,
            memory_limit_mib=512,
        )

        # Add EFS Volume to TaskDef
        web_app_task_def.add_volume(
            name="html",
            efs_volume_configuration=_ecs.EfsVolumeConfiguration(
                file_system_id=efs_share.file_system_id,
                transit_encryption="ENABLED",
                authorization_config=_ecs.AuthorizationConfig(
                    access_point_id=efs_ap_nginx.access_point_id
                )
            )
        )

        web_app_container = web_app_task_def.add_container(
            "webAppContainer",
            cpu=256,
            memory_limit_mib=512,
            environment={
                "github": "https://github.com/miztiik",
                "ko_fi": "https://ko-fi.com/miztiik"
            },
            image=_ecs.ContainerImage.from_registry(
                "nginx:latest"),
            logging=_ecs.LogDrivers.aws_logs(
                stream_prefix="mystique-automation-logs",
                log_retention=_logs.RetentionDays.ONE_DAY)
        )

        web_app_container.add_ulimits(
            _ecs.Ulimit(
                name=_ecs.UlimitName.NOFILE,
                soft_limit=65536,
                hard_limit=65536
            )
        )

        web_app_container.add_port_mappings(
            _ecs.PortMapping(
                container_port=80,
                protocol=_ecs.Protocol.TCP
            )
        )
        web_app_container.add_port_mappings(
            _ecs.PortMapping(
                container_port=443,
                protocol=_ecs.Protocol.TCP
            )
        )

        # Mount EFS Volume to Web Server Container
        web_app_container.add_mount_points(
            _ecs.MountPoint(
                container_path="/usr/share/nginx/html",
                read_only=False,
                source_volume="html"
            )
        )

        # Launch service and attach load balancer using CDK Pattern
        web_app_service = _ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "webSrv",
            platform_version=_ecs.FargatePlatformVersion.VERSION1_4,
            cluster=fargate_cluster,
            task_definition=web_app_task_def,
            assign_public_ip=False,
            public_load_balancer=True,
            listener_port=80,
            desired_count=1,
            # enable_ecs_managed_tags=True,
            health_check_grace_period=core.Duration.seconds(60),
            # cpu=1024,
            # memory_limit_mib=2048,
            # service_name="chatAppService",
        )

        # Outputs
        output_0 = core.CfnOutput(
            self,
            "AutomationFrom",
            value=f"{GlobalArgs.SOURCE_INFO}",
            description="To know more about this automation stack, check out our github page."
        )

        output_1 = core.CfnOutput(
            self, "ClusterNameOutput",
            value=f"{fargate_cluster.cluster_name}",
            description="To know more about this automation stack, check out our github page."
        )

        output_2 = core.CfnOutput(
            self,
            "webAppServiceUrl",
            value=f"http://{web_app_service.load_balancer.load_balancer_dns_name}",
            description="Use an utility like curl or an browser to access the web server."
        )
