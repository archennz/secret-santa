import * as cdk from "@aws-cdk/core";
import * as lambda from "@aws-cdk/aws-lambda";
import * as sources from "@aws-cdk/aws-lambda-event-sources";
import * as secret from "@aws-cdk/aws-secretsmanager";
import * as sfn from "@aws-cdk/aws-stepfunctions";
import * as tasks from "@aws-cdk/aws-stepfunctions-tasks";
import * as sqs from "@aws-cdk/aws-sqs";

export class CdkStack extends cdk.Stack {
  constructor(scope: cdk.Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const botTokenName: string = "SantaBotToken";
    const channelID: string = "C02AWHL5S3W";
    const secretRegion: string = "ap-southeast-2";

    const botToken = secret.Secret.fromSecretNameV2(
      this,
      "token",
      botTokenName
    );
    const queue = new sqs.Queue(this, "messageQueue");

    const queueSource = new sources.SqsEventSource(queue, { batchSize: 1 });

    const sendLambda = new lambda.DockerImageFunction(this, "sendLambda", {
      code: lambda.DockerImageCode.fromImageAsset("./src", {
        cmd: ["bot.send_message_handler"],
      }),
      environment: {
        SANTA_BOT_TOKEN: botTokenName,
        CHANNEL_ID: channelID,
        SECRET_REGION: secretRegion,
      },
    });

    const collectLambda = new lambda.DockerImageFunction(
      this,
      "collectLambda",
      {
        code: lambda.DockerImageCode.fromImageAsset("./src", {
          cmd: ["bot.collect_response_handler"],
        }),
        environment: {
          SANTA_BOT_TOKEN: botTokenName,
          CHANNEL_ID: channelID,
          SECRET_REGION: secretRegion,
          QUEUE_URL: queue.queueUrl,
        },
      }
    );

    queue.grantSendMessages(collectLambda);

    const santaLambda = new lambda.DockerImageFunction(this, "santaLambda", {
      code: lambda.DockerImageCode.fromImageAsset("./src", {
        cmd: ["bot.send_santa_message_handler"],
      }),
      environment: {
        SANTA_BOT_TOKEN: botTokenName,
        CHANNEL_ID: channelID,
        SECRET_REGION: secretRegion,
      },
      events: [queueSource],
      reservedConcurrentExecutions: 1,
      retryAttempts: 1,
      timeout: cdk.Duration.seconds(10),
    });

    botToken.grantRead(sendLambda);
    botToken.grantRead(collectLambda);
    botToken.grantRead(santaLambda);
    queue.grantConsumeMessages(santaLambda);

    const gatherParticipants = new tasks.LambdaInvoke(
      this,
      "sendFirstMessage",
      {
        lambdaFunction: sendLambda,
        outputPath: "$.Payload",
      }
    )
      .next(
        new sfn.Wait(this, "wait", {
          time: sfn.WaitTime.duration(cdk.Duration.seconds(5)),
        })
      )
      .next(
        new tasks.LambdaInvoke(this, "collectReactions", {
          lambdaFunction: collectLambda,
          outputPath: "$.Payload",
        })
      );

    const stateMachine = new sfn.StateMachine(this, "stateMachine", {
      definition: gatherParticipants,
    });
  }
}
