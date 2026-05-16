import * as path from "node:path";
import * as cdk from "aws-cdk-lib";
import { Construct } from "constructs";
import * as apigwv2 from "aws-cdk-lib/aws-apigatewayv2";
import * as integrations from "aws-cdk-lib/aws-apigatewayv2-integrations";
import * as dynamodb from "aws-cdk-lib/aws-dynamodb";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as s3 from "aws-cdk-lib/aws-s3";
import * as sqs from "aws-cdk-lib/aws-sqs";

export class OzStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const objectsBucket = new s3.Bucket(this, "ObjectsBucket", {
      encryption: s3.BucketEncryption.S3_MANAGED,
      intelligentTieringConfigurations: [{ name: "default" }],
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      removalPolicy: cdk.RemovalPolicy.RETAIN
    });

    const packsBucket = new s3.Bucket(this, "PacksBucket", {
      encryption: s3.BucketEncryption.S3_MANAGED,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      removalPolicy: cdk.RemovalPolicy.RETAIN
    });

    const rerankCache = new dynamodb.Table(this, "RerankCache", {
      partitionKey: { name: "cache_key", type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      timeToLiveAttribute: "expires_at",
      removalPolicy: cdk.RemovalPolicy.RETAIN
    });

    const crawlerQueue = new sqs.Queue(this, "CrawlerQueue", {
      visibilityTimeout: cdk.Duration.minutes(15),
      retentionPeriod: cdk.Duration.days(14)
    });

    const apiFunction = new lambda.Function(this, "ApiFunction", {
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: "lambda_entry.handler",
      code: lambda.Code.fromAsset(path.join(__dirname, "../../../../"), {
        exclude: [
          ".git",
          ".github",
          ".codo",
          "target",
          "dist",
          "node_modules",
          "infra/cdk/node_modules",
          "infra/cdk/cdk.out",
          "**/__pycache__",
          "**/.DS_Store"
        ]
      }),
      memorySize: 512,
      timeout: cdk.Duration.seconds(30),
      environment: {
        OZ_OBJECTS_BUCKET: objectsBucket.bucketName,
        OZ_PACKS_BUCKET: packsBucket.bucketName,
        OZ_RERANK_TABLE: rerankCache.tableName,
        OZ_CRAWLER_QUEUE_URL: crawlerQueue.queueUrl
      }
    });

    objectsBucket.grantReadWrite(apiFunction);
    packsBucket.grantReadWrite(apiFunction);
    rerankCache.grantReadWriteData(apiFunction);
    crawlerQueue.grantSendMessages(apiFunction);

    const httpApi = new apigwv2.HttpApi(this, "HttpApi", {
      defaultIntegration: new integrations.HttpLambdaIntegration("ApiIntegration", apiFunction)
    });

    new cdk.CfnOutput(this, "ApiUrl", { value: httpApi.url ?? "" });
    new cdk.CfnOutput(this, "ObjectsBucketName", { value: objectsBucket.bucketName });
    new cdk.CfnOutput(this, "PacksBucketName", { value: packsBucket.bucketName });
    new cdk.CfnOutput(this, "CrawlerQueueUrl", { value: crawlerQueue.queueUrl });
  }
}
