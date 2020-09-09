#!/usr/bin/env python3

from aws_cdk import core

from fargate_with_efs.stacks.back_end.vpc_stack import VpcStack
from fargate_with_efs.stacks.back_end.efs_stack import EfsStack
from fargate_with_efs.stacks.back_end.efs_content_creator_stack import EfsContentCreatorStack
from fargate_with_efs.stacks.back_end.fargate_with_efs_stack import FargateWithEfsStack


app = core.App()

# VPC Stack for hosting Secure API & Other resources
vpc_stack = VpcStack(
    app,
    "vpc-stack",
    description="Miztiik Automation: VPC to host resources for generating load on API"
)

# Create EFS
efs_stack = EfsStack(
    app,
    "efs-stack",
    vpc=vpc_stack.vpc,
    description="Miztiik Automation: Deploy AWS Elastic File System Stack"
)

# Use Lambda with API Gateway to create content in EFS
efs_content_creator_stack = EfsContentCreatorStack(
    app,
    "efs-content-creator-stack",
    vpc=vpc_stack.vpc,
    efs_sg=efs_stack.efs_sg,
    efs_share=efs_stack.efs_share,
    efs_ap_nginx=efs_stack.efs_ap_nginx,
    stack_log_level="INFO",
    back_end_api_name="efs-content-creator",
    description="Miztiik Automation: Use Lambda with API Gateway to create content in EFS"
)

# Persistent storage with containerized workload like Fargate
fargate_with_efs = FargateWithEfsStack(
    app,
    "fargate-with-efs",
    custom_vpc=vpc_stack.vpc,
    efs_share=efs_stack.efs_share,
efs_ap_nginx=efs_stack.efs_ap_nginx,
    enable_container_insights=True,
    description="Persistent storage with containerized workload like Fargate"
)

# Stack Level Tagging
core.Tag.add(app, key="Owner",
             value=app.node.try_get_context("owner"))
core.Tag.add(app, key="OwnerProfile",
             value=app.node.try_get_context("github_profile"))
core.Tag.add(app, key="Project",
             value=app.node.try_get_context("service_name"))
core.Tag.add(app, key="GithubRepo",
             value=app.node.try_get_context("github_repo_url"))
core.Tag.add(app, key="Udemy",
             value=app.node.try_get_context("udemy_profile"))
core.Tag.add(app, key="SkillShare",
             value=app.node.try_get_context("skill_profile"))
core.Tag.add(app, key="AboutMe",
             value=app.node.try_get_context("about_me"))
core.Tag.add(app, key="BuyMeCoffee",
             value=app.node.try_get_context("ko_fi"))

app.synth()
