import * as cdk from "@aws-cdk/core";
import * as lambda from "@aws-cdk/aws-lambda";
import * as sources from "@aws-cdk/aws-lambda-event-sources";
import * as secret from "@aws-cdk/aws-secretsmanager";
import * as sfn from "@aws-cdk/aws-stepfunctions";
import * as tasks from "@aws-cdk/aws-stepfunctions-tasks";
import * as sqs from "@aws-cdk/aws-sqs";
import * as cloudwatch from "@aws-cdk/aws-cloudwatch";

export class CdkStack extends cdk.Stack {
  constructor(scope: cdk.Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // bot config
    const botTokenName: string = this.node.tryGetContext("botTokenName");
    const secretRegion: string = this.node.tryGetContext("secretRegion");
    const channelID: string = this.node.tryGetContext("channelID");

    // wait time for assigning secret santa pairs
    const waitTime: cdk.Duration = cdk.Duration.days(7);

    // get bot token
    const botToken = secret.Secret.fromSecretNameV2(
      this,
      "token",
      botTokenName
    );

    // setting up queue
    const deadLetterQueue = new sqs.Queue(this, "deadLetterQueue");
    const queue = new sqs.Queue(this, "messageQueue", {
      deadLetterQueue: {
        maxReceiveCount: 3,
        queue: deadLetterQueue,
      },
    });
    const queueSource = new sources.SqsEventSource(queue, { batchSize: 1 });

    // setting up the lambda
    // this lambda sends the initial message
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

    botToken.grantRead(sendLambda);

    // this lambda collects the reactions and drops the secret santa pairs into the queue
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

    botToken.grantRead(collectLambda);
    queue.grantSendMessages(collectLambda);

    // this lambda polls from the queue and sends the messages to slack with the santa pairings
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

    botToken.grantRead(santaLambda);
    queue.grantConsumeMessages(santaLambda);

    // step function for sending initial message then waiting then closing submission
    // then depositing the secret santa pairs into the queue
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
          time: sfn.WaitTime.duration(waitTime),
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

    // alarm for DLQ
    const metric = deadLetterQueue.metricNumberOfMessagesReceived();
    const alarm = new cloudwatch.Alarm(this, "dlqAlarm", {
      alarmDescription:
        "There are messages in Dead Letter Queue, some slack bot messages are not sent",
      evaluationPeriods: 1,
      threshold: 1,
      metric: metric,
    });
  }
}
