import * as cdk from "@aws-cdk/core";
import * as lambda from "@aws-cdk/aws-lambda";
import * as secret from "@aws-cdk/aws-secretsmanager";

export class CdkStack extends cdk.Stack {
  constructor(scope: cdk.Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const botTokenName: string = "SantaBotToken";
    const channelID: string = "C02AWHL5S3W";
    const secretRegion: string = "ap-southeast-2"

    const botToken = secret.Secret.fromSecretCompleteArn(
      this,
      "token",
      "arn:aws:secretsmanager:ap-southeast-2:519222315617:secret:SantaBotToken-HuEpdd"
    );

    const sendLambda = new lambda.DockerImageFunction(this, "sendLambda", {
      code: lambda.DockerImageCode.fromImageAsset("./src", {
        cmd: ["bot.send_message_handler"],
      }),
      environment: {
        SANTA_BOT_TOKEN: botTokenName,
        CHANNEL_ID: channelID,
        SECRET_REGION: secretRegion
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
          SECRET_REGION: secretRegion
        },
      }
    );

    const santaLambda = new lambda.DockerImageFunction(this, "santaLambda", {
      code: lambda.DockerImageCode.fromImageAsset("./src", {
        cmd: ["bot.send_santa_message_handler"],
      }),
      environment: {
        SANTA_BOT_TOKEN: botTokenName,
        CHANNEL_ID: channelID,
        SECRET_REGION: secretRegion
      },
    });


    botToken.grantRead(sendLambda);
    botToken.grantRead(collectLambda);
    botToken.grantRead(santaLambda);
  }
}
