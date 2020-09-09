from aws_cdk import aws_apigateway as _apigw
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_iam as _iam
from aws_cdk import aws_ec2 as _ec2
from aws_cdk import aws_logs as _logs

from aws_cdk import core

import os


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


class EfsContentCreatorStack(core.Stack):

    def __init__(
        self,
        scope: core.Construct,
        id: str,
        vpc,
        efs_sg,
        efs_share,
        efs_ap_nginx,
        stack_log_level: str,
        back_end_api_name: str,
        **kwargs
    ) -> None:
        super().__init__(scope, id, **kwargs)

        # Create Serverless Event Processor using Lambda):
        # Read Lambda Code):
        try:
            with open("fargate_with_efs/stacks/back_end/lambda_src/serverless_greeter.py", mode="r") as f:
                greeter_fn_code = f.read()
        except OSError as e:
            print("Unable to read Lambda Function Code")
            raise e

        efs_mnt_path = "/mnt/html"

        greeter_fn = _lambda.Function(
            self,
            "secureGreeterFn",
            function_name=f"greeter_fn_{id}",
            runtime=_lambda.Runtime.PYTHON_3_7,
            handler="index.lambda_handler",
            code=_lambda.InlineCode(greeter_fn_code),
            current_version_options={
                "removal_policy": core.RemovalPolicy.DESTROY,  # retain old versions
                "retry_attempts": 1,
                "description": "Mystique Factory Build Version"
            },
            timeout=core.Duration.seconds(15),
            reserved_concurrent_executions=20,
            retry_attempts=1,
            environment={
                "LOG_LEVEL": f"{stack_log_level}",
                "Environment": "Production",
                "ANDON_CORD_PULLED": "False",
                "RANDOM_SLEEP_ENABLED": "False",
                "EFS_MNT_PATH": efs_mnt_path
            },
            description="A simple greeter function, which responds with a timestamp",
            vpc=vpc,
            vpc_subnets=_ec2.SubnetType.PRIVATE,
            security_groups=[efs_sg],
            filesystem=_lambda.FileSystem.from_efs_access_point(
                efs_ap_nginx, efs_mnt_path)
        )
        greeter_fn_version = greeter_fn.latest_version
        greeter_fn_dev_alias = _lambda.Alias(
            self,
            "greeterFnMystiqueAutomationAlias",
            alias_name="MystiqueAutomation",
            version=greeter_fn_version,
            description="Mystique Factory Build Version to ingest content from API GW to EFS",
            retry_attempts=1
        )

        # Create Custom Loggroup
        greeter_fn_lg = _logs.LogGroup(
            self,
            "greeterFnLoggroup",
            log_group_name=f"/aws/lambda/{greeter_fn.function_name}",
            retention=_logs.RetentionDays.ONE_WEEK,
            removal_policy=core.RemovalPolicy.DESTROY
        )

# %%
        wa_api_logs = _logs.LogGroup(
            self,
            "waApiLogs",
            log_group_name=f"/aws/apigateway/{back_end_api_name}/access_logs",
            removal_policy=core.RemovalPolicy.DESTROY,
            retention=_logs.RetentionDays.ONE_DAY
        )

        #######################################
        ##    CONFIG FOR API STAGE : PROD    ##
        #######################################

        # Add API GW front end for the Lambda
        prod_api_stage_options = _apigw.StageOptions(
            stage_name="prod",
            throttling_rate_limit=10,
            throttling_burst_limit=100,
            # Log full requests/responses data
            data_trace_enabled=True,
            # Enable Detailed CloudWatch Metrics
            metrics_enabled=True,
            logging_level=_apigw.MethodLoggingLevel.INFO,
            access_log_destination=_apigw.LogGroupLogDestination(wa_api_logs),
            variables={
                "lambdaAlias": "prod",
                "appOwner": "Mystique"
            }
        )

        # Create API Gateway
        wa_api = _apigw.RestApi(
            self,
            "backEnd01Api",
            rest_api_name=f"{back_end_api_name}",
            deploy_options=prod_api_stage_options,
            endpoint_types=[
                _apigw.EndpointType.EDGE
            ],
            description=f"{GlobalArgs.OWNER}: API Best Practices. This stack deploys an API and integrates with Lambda $LATEST alias."
        )

        wa_api_res = wa_api.root.add_resource("well-architected-api")
        create_content = wa_api_res.add_resource("create-content")

        # Add POST method to API
        create_content_get = create_content.add_method(
            http_method="POST",
            request_parameters={
                "method.request.header.InvocationType": True,
                "method.request.path.mystique": True
            },
            integration=_apigw.LambdaIntegration(
                handler=greeter_fn,
                proxy=True
            )
        )

        # Outputs
        output_0 = core.CfnOutput(
            self,
            "AutomationFrom",
            value=f"{GlobalArgs.SOURCE_INFO}",
            description="To know more about this automation stack, check out our github page."
        )

        output_1 = core.CfnOutput(
            self,
            "ContentCreatorApiUrl",
            value=f"curl -X POST -H 'Content-Type: text/plain' -d 'Hello again :)' {create_content.url}",
            description='Use an utility like curl to add content to EFS. For ex: curl -X POST -H "Content-Type: text/plain" -d "Hello again :)" ${API_URL}'
        )
