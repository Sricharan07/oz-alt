import * as path from "node:path";
import * as cdk from "aws-cdk-lib";
import { Construct } from "constructs";
import * as apigwv2 from "aws-cdk-lib/aws-apigatewayv2";
import * as integrations from "aws-cdk-lib/aws-apigatewayv2-integrations";
import * as budgets from "aws-cdk-lib/aws-budgets";
import * as dynamodb from "aws-cdk-lib/aws-dynamodb";
import * as ec2 from "aws-cdk-lib/aws-ec2";
import * as events from "aws-cdk-lib/aws-events";
import * as targets from "aws-cdk-lib/aws-events-targets";
import * as iam from "aws-cdk-lib/aws-iam";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as lambdaEventSources from "aws-cdk-lib/aws-lambda-event-sources";
import * as rds from "aws-cdk-lib/aws-rds";
import * as s3 from "aws-cdk-lib/aws-s3";
import * as secretsmanager from "aws-cdk-lib/aws-secretsmanager";
import * as sqs from "aws-cdk-lib/aws-sqs";

export class OzStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const budgetAlertEmail = new cdk.CfnParameter(this, "BudgetAlertEmail", {
      type: "String",
      default: "alerts@example.com",
      description: "Email address for the Oz beta $200 monthly budget alert."
    });

    const objectsBucket = new s3.Bucket(this, "ObjectsBucket", {
      encryption: s3.BucketEncryption.S3_MANAGED,
      intelligentTieringConfigurations: [{ name: "default" }],
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      removalPolicy: cdk.RemovalPolicy.RETAIN
    });

    const packsBucket = new s3.Bucket(this, "PacksBucket", {
      encryption: s3.BucketEncryption.S3_MANAGED,
      blockPublicAccess: new s3.BlockPublicAccess({
        blockPublicAcls: true,
        ignorePublicAcls: true,
        blockPublicPolicy: false,
        restrictPublicBuckets: false
      }),
      removalPolicy: cdk.RemovalPolicy.RETAIN
    });
    packsBucket.addToResourcePolicy(new iam.PolicyStatement({
      actions: ["s3:GetObject"],
      principals: [new iam.AnyPrincipal()],
      resources: [packsBucket.arnForObjects("packs/*")]
    }));

    const rerankCache = new dynamodb.Table(this, "RerankCache", {
      partitionKey: { name: "cache_key", type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      timeToLiveAttribute: "expires_at",
      removalPolicy: cdk.RemovalPolicy.RETAIN
    });

    const jwtSecret = new secretsmanager.Secret(this, "JwtSecret", {
      generateSecretString: {
        passwordLength: 48,
        excludePunctuation: true
      }
    });

    const vpc = new ec2.Vpc(this, "Vpc", {
      maxAzs: 2,
      natGateways: 0,
      subnetConfiguration: [
        {
          name: "isolated",
          subnetType: ec2.SubnetType.PRIVATE_ISOLATED,
          cidrMask: 24
        }
      ]
    });

    const databaseSecurityGroup = new ec2.SecurityGroup(this, "DatabaseSecurityGroup", {
      vpc,
      allowAllOutbound: false
    });

    const databaseSubnets = vpc.selectSubnets({
      subnetType: ec2.SubnetType.PRIVATE_ISOLATED
    });

    const databaseSubnetGroup = new rds.CfnDBSubnetGroup(this, "DatabaseSubnetGroup", {
      dbSubnetGroupDescription: "Private subnets for Oz Aurora Serverless v2",
      subnetIds: databaseSubnets.subnetIds
    });

    const database = new rds.CfnDBCluster(this, "RegistryDatabase", {
      engine: "aurora-postgresql",
      engineMode: "provisioned",
      engineVersion: "16.6",
      databaseName: "oz",
      masterUsername: "oz_admin",
      manageMasterUserPassword: true,
      dbSubnetGroupName: databaseSubnetGroup.ref,
      vpcSecurityGroupIds: [databaseSecurityGroup.securityGroupId],
      storageEncrypted: true,
      backupRetentionPeriod: 7,
      deletionProtection: false,
      enableHttpEndpoint: true,
      serverlessV2ScalingConfiguration: {
        minCapacity: 0.5,
        maxCapacity: 2
      },
      enableCloudwatchLogsExports: ["postgresql"]
    });
    database.applyRemovalPolicy(cdk.RemovalPolicy.RETAIN);

    const databaseInstance = new rds.CfnDBInstance(this, "RegistryDatabaseWriter", {
      dbClusterIdentifier: database.ref,
      dbInstanceClass: "db.serverless",
      engine: "aurora-postgresql",
      publiclyAccessible: false
    });
    databaseInstance.addDependency(database);
    databaseInstance.applyRemovalPolicy(cdk.RemovalPolicy.RETAIN);

    const crawlerDlq = new sqs.Queue(this, "CrawlerDeadLetterQueue", {
      retentionPeriod: cdk.Duration.days(14)
    });

    const crawlerQueue = new sqs.Queue(this, "CrawlerQueue", {
      visibilityTimeout: cdk.Duration.minutes(15),
      retentionPeriod: cdk.Duration.days(14),
      deadLetterQueue: {
        queue: crawlerDlq,
        maxReceiveCount: 3
      }
    });

    const assetCode = lambda.Code.fromAsset(path.join(__dirname, "../../../../"), {
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
    });

    const apiFunction = new lambda.Function(this, "ApiFunction", {
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: "lambda_entry.handler",
      code: assetCode,
      memorySize: 512,
      timeout: cdk.Duration.seconds(30),
      environment: {
        OZ_OBJECTS_BUCKET: objectsBucket.bucketName,
        OZ_PACKS_BUCKET: packsBucket.bucketName,
        OZ_CATALOG_BUCKET: packsBucket.bucketName,
        OZ_CATALOG_KEY: "catalog.json",
        OZ_PACK_PREFIX: "packs",
        OZ_PACK_PUBLIC_BASE_URL: packsBucket.urlForObject("packs"),
        OZ_RERANK_TABLE: rerankCache.tableName,
        OZ_CRAWLER_QUEUE_URL: crawlerQueue.queueUrl,
        OZ_DB_RESOURCE_ARN: database.attrDbClusterArn,
        OZ_DB_SECRET_ARN: database.attrMasterUserSecretSecretArn,
        OZ_DB_NAME: "oz",
        OZ_JWT_SECRET_ARN: jwtSecret.secretArn,
        OZ_REQUIRE_AUTH: "true"
      }
    });

    objectsBucket.grantReadWrite(apiFunction);
    packsBucket.grantReadWrite(apiFunction);
    rerankCache.grantReadWriteData(apiFunction);
    crawlerQueue.grantSendMessages(apiFunction);
    jwtSecret.grantRead(apiFunction);
    apiFunction.addToRolePolicy(new iam.PolicyStatement({
      actions: [
        "rds-data:ExecuteStatement",
        "rds-data:BatchExecuteStatement",
        "secretsmanager:GetSecretValue"
      ],
      resources: [
        database.attrDbClusterArn,
        database.attrMasterUserSecretSecretArn
      ]
    }));

    const crawlerFunction = new lambda.Function(this, "CrawlerFunction", {
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: "lambda_crawler_entry.handler",
      code: assetCode,
      memorySize: 1024,
      timeout: cdk.Duration.minutes(15),
      environment: {
        OZ_OBJECTS_BUCKET: objectsBucket.bucketName,
        OZ_PACKS_BUCKET: packsBucket.bucketName,
        OZ_CATALOG_BUCKET: packsBucket.bucketName,
        OZ_CATALOG_KEY: "catalog.json",
        OZ_PACK_PREFIX: "packs",
        OZ_PACK_PUBLIC_BASE_URL: packsBucket.urlForObject("packs"),
        OZ_CRAWLER_QUEUE_URL: crawlerQueue.queueUrl,
        OZ_DB_RESOURCE_ARN: database.attrDbClusterArn,
        OZ_DB_SECRET_ARN: database.attrMasterUserSecretSecretArn,
        OZ_DB_NAME: "oz",
        OZ_JWT_SECRET_ARN: jwtSecret.secretArn
      }
    });
    crawlerQueue.grantConsumeMessages(crawlerFunction);
    crawlerQueue.grantSendMessages(crawlerFunction);
    objectsBucket.grantReadWrite(crawlerFunction);
    packsBucket.grantReadWrite(crawlerFunction);
    jwtSecret.grantRead(crawlerFunction);
    crawlerFunction.addToRolePolicy(new iam.PolicyStatement({
      actions: [
        "rds-data:ExecuteStatement",
        "rds-data:BatchExecuteStatement",
        "secretsmanager:GetSecretValue"
      ],
      resources: [
        database.attrDbClusterArn,
        database.attrMasterUserSecretSecretArn
      ]
    }));
    crawlerFunction.addEventSource(new lambdaEventSources.SqsEventSource(crawlerQueue, {
      batchSize: 1
    }));

    new events.Rule(this, "DailyRecrawlSchedule", {
      schedule: events.Schedule.rate(cdk.Duration.days(1)),
      targets: [
        new targets.SqsQueue(crawlerQueue, {
          message: events.RuleTargetInput.fromObject({
            type: "scheduled_recrawl",
            status: "queued"
          })
        })
      ]
    });

    const httpApi = new apigwv2.HttpApi(this, "HttpApi", {
      defaultIntegration: new integrations.HttpLambdaIntegration("ApiIntegration", apiFunction)
    });

    new budgets.CfnBudget(this, "BetaBudget", {
      budget: {
        budgetName: "oz-beta-200-usd",
        budgetLimit: {
          amount: 200,
          unit: "USD"
        },
        budgetType: "COST",
        timeUnit: "MONTHLY"
      },
      notificationsWithSubscribers: [
        {
          notification: {
            comparisonOperator: "GREATER_THAN",
            notificationType: "ACTUAL",
            threshold: 100,
            thresholdType: "PERCENTAGE"
          },
          subscribers: [
            {
              address: budgetAlertEmail.valueAsString,
              subscriptionType: "EMAIL"
            }
          ]
        }
      ]
    });

    new cdk.CfnOutput(this, "ApiUrl", { value: httpApi.url ?? "" });
    new cdk.CfnOutput(this, "ObjectsBucketName", { value: objectsBucket.bucketName });
    new cdk.CfnOutput(this, "PacksBucketName", { value: packsBucket.bucketName });
    new cdk.CfnOutput(this, "CrawlerQueueUrl", { value: crawlerQueue.queueUrl });
    new cdk.CfnOutput(this, "CrawlerDeadLetterQueueUrl", { value: crawlerDlq.queueUrl });
    new cdk.CfnOutput(this, "DatabaseClusterArn", { value: database.attrDbClusterArn });
    new cdk.CfnOutput(this, "DatabaseSecretArn", { value: database.attrMasterUserSecretSecretArn });
  }
}
