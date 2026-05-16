import * as path from "node:path";
import * as cdk from "aws-cdk-lib";
import { Construct } from "constructs";
import * as acm from "aws-cdk-lib/aws-certificatemanager";
import * as apigwv2 from "aws-cdk-lib/aws-apigatewayv2";
import * as integrations from "aws-cdk-lib/aws-apigatewayv2-integrations";
import * as budgets from "aws-cdk-lib/aws-budgets";
import * as dynamodb from "aws-cdk-lib/aws-dynamodb";
import * as ec2 from "aws-cdk-lib/aws-ec2";
import * as ecs from "aws-cdk-lib/aws-ecs";
import * as events from "aws-cdk-lib/aws-events";
import * as targets from "aws-cdk-lib/aws-events-targets";
import * as iam from "aws-cdk-lib/aws-iam";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as lambdaEventSources from "aws-cdk-lib/aws-lambda-event-sources";
import * as logs from "aws-cdk-lib/aws-logs";
import * as rds from "aws-cdk-lib/aws-rds";
import * as s3 from "aws-cdk-lib/aws-s3";
import * as secretsmanager from "aws-cdk-lib/aws-secretsmanager";
import * as sqs from "aws-cdk-lib/aws-sqs";

export class OzStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const customDomainName = readOptionalEnv("OZ_CUSTOM_DOMAIN_NAME");
    const customDomainCertificateArn = readOptionalEnv("OZ_CUSTOM_DOMAIN_CERT_ARN");
    if (customDomainName && !customDomainCertificateArn) {
      throw new Error(
        "OZ_CUSTOM_DOMAIN_CERT_ARN is required when OZ_CUSTOM_DOMAIN_NAME is set"
      );
    }
    if (customDomainCertificateArn && !customDomainName) {
      throw new Error(
        "OZ_CUSTOM_DOMAIN_NAME is required when OZ_CUSTOM_DOMAIN_CERT_ARN is set"
      );
    }
    const customDomainCertificateArnValue = customDomainCertificateArn ?? "";

    const budgetAlertEmail = new cdk.CfnParameter(this, "BudgetAlertEmail", {
      type: "String",
      default: "alerts@example.com",
      description: "Email address for the Oz beta $200 monthly budget alert."
    });
    const requireOAuth = new cdk.CfnParameter(this, "RequireOAuth", {
      type: "String",
      default: "true",
      allowedValues: ["true", "false"],
      description: "Require a configured OAuth device provider for CLI login."
    });
    const oauthDeviceAuthUrl = new cdk.CfnParameter(this, "OAuthDeviceAuthUrl", {
      type: "String",
      default: "",
      description: "OAuth device authorization endpoint."
    });
    const oauthTokenUrl = new cdk.CfnParameter(this, "OAuthTokenUrl", {
      type: "String",
      default: "",
      description: "OAuth token endpoint."
    });
    const oauthClientId = new cdk.CfnParameter(this, "OAuthClientId", {
      type: "String",
      default: "",
      description: "OAuth device flow client id."
    });
    const oauthScope = new cdk.CfnParameter(this, "OAuthScope", {
      type: "String",
      default: "openid profile email",
      description: "OAuth scopes requested by the CLI device flow."
    });
    const packSigningKey = new cdk.CfnParameter(this, "PackSigningKey", {
      type: "String",
      default: "",
      noEcho: true,
      description: "32-byte Ed25519 signing seed as hex/base64url/base64 for packs built in Lambda."
    });
    const packSigningKeyId = new cdk.CfnParameter(this, "PackSigningKeyId", {
      type: "String",
      default: "prod",
      description: "Key id written into signed pack manifests."
    });
    const packVerifyKey = new cdk.CfnParameter(this, "PackVerifyKey", {
      type: "String",
      default: "",
      description: "32-byte Ed25519 public verification key as hex/base64url/base64."
    });

    const objectsBucket = new s3.Bucket(this, "ObjectsBucket", {
      encryption: s3.BucketEncryption.S3_MANAGED,
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
    const openAiApiKeySecret = new secretsmanager.Secret(this, "OpenAiApiKeySecret", {
      generateSecretString: {
        passwordLength: 48,
        excludePunctuation: true
      },
      description: "OpenAI API key for Oz embeddings and reranking. Replace the generated value with a real sk-* key."
    });

    const vpc = new ec2.Vpc(this, "Vpc", {
      maxAzs: 2,
      natGateways: 0,
      subnetConfiguration: [
        {
          name: "public",
          subnetType: ec2.SubnetType.PUBLIC,
          cidrMask: 24
        },
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
      visibilityTimeout: cdk.Duration.minutes(15),
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

    const repoRoot = path.join(__dirname, "../../../../");
    const assetCode = lambda.Code.fromAsset(repoRoot, {
      ignoreMode: cdk.IgnoreMode.GLOB,
      exclude: [
        ".git",
        ".git/**",
        "**/.git",
        "**/.git/**",
        ".github",
        ".github/**",
        ".codo",
        ".codo/**",
        "target",
        "target/**",
        "dist",
        "dist/**",
        "node_modules",
        "node_modules/**",
        "infra/cdk/node_modules",
        "infra/cdk/node_modules/**",
        "infra/cdk/cdk.out",
        "infra/cdk/cdk.out/**",
        "cdk.out",
        "cdk.out/**",
        "**/cdk.out/**",
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
        OPENAI_API_KEY_SECRET_ARN: openAiApiKeySecret.secretArn,
        OZ_REQUIRE_AUTH: "true",
        OZ_REQUIRE_OAUTH: requireOAuth.valueAsString,
        OZ_OAUTH_DEVICE_AUTH_URL: oauthDeviceAuthUrl.valueAsString,
        OZ_OAUTH_TOKEN_URL: oauthTokenUrl.valueAsString,
        OZ_OAUTH_CLIENT_ID: oauthClientId.valueAsString,
        OZ_OAUTH_SCOPE: oauthScope.valueAsString,
        OZ_PACK_VERIFY_KEY: packVerifyKey.valueAsString,
        OZ_PACK_REQUIRE_SIGNATURE: "true"
      }
    });

    objectsBucket.grantReadWrite(apiFunction);
    packsBucket.grantReadWrite(apiFunction);
    rerankCache.grantReadWriteData(apiFunction);
    crawlerQueue.grantSendMessages(apiFunction);
    jwtSecret.grantRead(apiFunction);
    openAiApiKeySecret.grantRead(apiFunction);
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
        OZ_JWT_SECRET_ARN: jwtSecret.secretArn,
        OPENAI_API_KEY_SECRET_ARN: openAiApiKeySecret.secretArn,
        OZ_PACK_SIGNING_KEY: packSigningKey.valueAsString,
        OZ_PACK_SIGNING_KEY_ID: packSigningKeyId.valueAsString,
        OZ_PACK_VERIFY_KEY: packVerifyKey.valueAsString,
        OZ_PACK_REQUIRE_SIGNATURE: "true"
      }
    });
    crawlerQueue.grantConsumeMessages(crawlerFunction);
    crawlerQueue.grantSendMessages(crawlerFunction);
    objectsBucket.grantReadWrite(crawlerFunction);
    packsBucket.grantReadWrite(crawlerFunction);
    jwtSecret.grantRead(crawlerFunction);
    openAiApiKeySecret.grantRead(crawlerFunction);
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

    const crawlerSubnets = vpc.selectSubnets({
      subnetType: ec2.SubnetType.PUBLIC
    });
    const crawlerTaskSecurityGroup = new ec2.SecurityGroup(this, "CrawlerTaskSecurityGroup", {
      vpc,
      allowAllOutbound: true
    });
    const crawlerCluster = new ecs.Cluster(this, "CrawlerCluster", {
      vpc,
      enableFargateCapacityProviders: true,
      containerInsightsV2: ecs.ContainerInsights.ENABLED
    });
    const crawlerTaskDefinition = new ecs.FargateTaskDefinition(this, "CrawlerFargateTask", {
      cpu: 1024,
      memoryLimitMiB: 4096
    });
    const crawlerLogGroup = new logs.LogGroup(this, "CrawlerFargateLogs", {
      retention: logs.RetentionDays.ONE_MONTH,
      removalPolicy: cdk.RemovalPolicy.DESTROY
    });
    const crawlerContainerName = "CrawlerContainer";
    crawlerTaskDefinition.addContainer(crawlerContainerName, {
      image: ecs.ContainerImage.fromAsset(repoRoot, {
        file: "Dockerfile.crawler",
        ignoreMode: cdk.IgnoreMode.GLOB,
        exclude: [
          ".git",
          ".git/**",
          "**/.git",
          "**/.git/**",
          ".github",
          ".github/**",
          ".codo",
          ".codo/**",
          "dist",
          "dist/**",
          "target",
          "target/**",
          "node_modules",
          "node_modules/**",
          "infra/cdk/node_modules",
          "infra/cdk/node_modules/**",
          "infra/cdk/cdk.out",
          "infra/cdk/cdk.out/**",
          "cdk.out",
          "cdk.out/**",
          "**/cdk.out/**",
          "registry/packs",
          "registry/packs/**",
          "**/__pycache__",
          "**/.DS_Store"
        ]
      }),
      logging: ecs.LogDrivers.awsLogs({
        streamPrefix: "oz-crawler-fargate",
        logGroup: crawlerLogGroup
      }),
      environment: {
        OZ_OBJECTS_BUCKET: objectsBucket.bucketName,
        OZ_PACKS_BUCKET: packsBucket.bucketName,
        OZ_CATALOG_BUCKET: packsBucket.bucketName,
        OZ_CATALOG_KEY: "catalog.json",
        OZ_PACK_PREFIX: "packs",
        OZ_PACK_PUBLIC_BASE_URL: packsBucket.urlForObject("packs"),
        OZ_DB_RESOURCE_ARN: database.attrDbClusterArn,
        OZ_DB_SECRET_ARN: database.attrMasterUserSecretSecretArn,
        OZ_DB_NAME: "oz",
        OZ_JWT_SECRET_ARN: jwtSecret.secretArn,
        OPENAI_API_KEY_SECRET_ARN: openAiApiKeySecret.secretArn,
        OZ_PACK_SIGNING_KEY: packSigningKey.valueAsString,
        OZ_PACK_SIGNING_KEY_ID: packSigningKeyId.valueAsString,
        OZ_PACK_VERIFY_KEY: packVerifyKey.valueAsString,
        OZ_PACK_REQUIRE_SIGNATURE: "true"
      }
    });
    objectsBucket.grantReadWrite(crawlerTaskDefinition.taskRole);
    packsBucket.grantReadWrite(crawlerTaskDefinition.taskRole);
    jwtSecret.grantRead(crawlerTaskDefinition.taskRole);
    openAiApiKeySecret.grantRead(crawlerTaskDefinition.taskRole);
    crawlerTaskDefinition.addToTaskRolePolicy(new iam.PolicyStatement({
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

    const fargateFailoverFunction = new lambda.Function(this, "CrawlerFargateFailoverFunction", {
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: "lambda_fargate_entry.handler",
      code: assetCode,
      memorySize: 256,
      timeout: cdk.Duration.minutes(2),
      environment: {
        OZ_PACKS_BUCKET: packsBucket.bucketName,
        OZ_ADMIN_BUCKET: packsBucket.bucketName,
        OZ_ADMIN_PREFIX: "admin",
        OZ_FARGATE_CLUSTER: crawlerCluster.clusterName,
        OZ_FARGATE_TASK_DEFINITION: crawlerTaskDefinition.taskDefinitionArn,
        OZ_FARGATE_SUBNETS: crawlerSubnets.subnetIds.join(","),
        OZ_FARGATE_SECURITY_GROUP: crawlerTaskSecurityGroup.securityGroupId,
        OZ_FARGATE_CONTAINER: crawlerContainerName,
        OZ_FARGATE_CAPACITY_PROVIDER: "FARGATE_SPOT"
      }
    });
    crawlerDlq.grantConsumeMessages(fargateFailoverFunction);
    packsBucket.grantReadWrite(fargateFailoverFunction);
    fargateFailoverFunction.addToRolePolicy(new iam.PolicyStatement({
      actions: ["ecs:RunTask"],
      resources: [crawlerTaskDefinition.taskDefinitionArn]
    }));
    const passRoleArns = [crawlerTaskDefinition.taskRole.roleArn];
    if (crawlerTaskDefinition.executionRole) {
      passRoleArns.push(crawlerTaskDefinition.executionRole.roleArn);
    }
    fargateFailoverFunction.addToRolePolicy(new iam.PolicyStatement({
      actions: ["iam:PassRole"],
      resources: passRoleArns
    }));
    fargateFailoverFunction.addEventSource(new lambdaEventSources.SqsEventSource(crawlerDlq, {
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

    const customDomain = customDomainName
      ? new apigwv2.DomainName(this, "CustomDomainName", {
          domainName: customDomainName,
          certificate: acm.Certificate.fromCertificateArn(
            this,
            "CustomDomainCertificate",
            customDomainCertificateArnValue
          )
        })
      : undefined;

    const httpApiProps: apigwv2.HttpApiProps = {
      defaultIntegration: new integrations.HttpLambdaIntegration("ApiIntegration", apiFunction)
    };
    if (customDomain) {
      httpApiProps.defaultDomainMapping = {
        domainName: customDomain
      };
      httpApiProps.disableExecuteApiEndpoint = true;
    }

    const httpApi = new apigwv2.HttpApi(this, "HttpApi", httpApiProps);

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

    new cdk.CfnOutput(this, "ApiGatewayExecuteUrl", { value: httpApi.url ?? "" });
    new cdk.CfnOutput(this, "ApiUrl", {
      value: customDomain ? `https://${customDomainName}` : (httpApi.url ?? "")
    });
    if (customDomain) {
      new cdk.CfnOutput(this, "CustomDomainName", { value: customDomainName });
      new cdk.CfnOutput(this, "CloudflareCnameTarget", {
        value: customDomain.regionalDomainName
      });
      new cdk.CfnOutput(this, "CloudflareHostedZoneId", {
        value: customDomain.regionalHostedZoneId
      });
    }
    new cdk.CfnOutput(this, "ObjectsBucketName", { value: objectsBucket.bucketName });
    new cdk.CfnOutput(this, "PacksBucketName", { value: packsBucket.bucketName });
    new cdk.CfnOutput(this, "CrawlerQueueUrl", { value: crawlerQueue.queueUrl });
    new cdk.CfnOutput(this, "CrawlerDeadLetterQueueUrl", { value: crawlerDlq.queueUrl });
    new cdk.CfnOutput(this, "CrawlerClusterName", { value: crawlerCluster.clusterName });
    new cdk.CfnOutput(this, "CrawlerFargateTaskArn", { value: crawlerTaskDefinition.taskDefinitionArn });
    new cdk.CfnOutput(this, "DatabaseClusterArn", { value: database.attrDbClusterArn });
    new cdk.CfnOutput(this, "DatabaseSecretArn", { value: database.attrMasterUserSecretSecretArn });
    new cdk.CfnOutput(this, "OpenAiApiKeySecretArn", { value: openAiApiKeySecret.secretArn });
  }
}

function readOptionalEnv(name: string): string | undefined {
  const value = process.env[name]?.trim();
  return value ? value : undefined;
}
