#!/usr/bin/env python3

from aws_cdk import core

from fargate_with_efs.fargate_with_efs_stack import FargateWithEfsStack


app = core.App()
FargateWithEfsStack(app, "fargate-with-efs")

app.synth()
