import * as cdk from "aws-cdk-lib";
import { OzStack } from "../lib/oz-stack";

const app = new cdk.App();

new OzStack(app, "OzStack", {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION ?? "us-east-1"
  }
});

