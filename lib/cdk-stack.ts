import * as cdk from "@aws-cdk/core";
import * as lambda from "@aws-cdk/aws-lambda";
import * as secret from "@aws-cdk/aws-secretsmanager";

export class CdkStack extends cdk.Stack {
  constructor(scope: cdk.Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const botToken = secret.Secret.fromSecretCompleteArn(
      this,
      "token",
      "arn:aws:secretsmanager:ap-southeast-2:519222315617:secret:SantaBotToken-HuEpdd"
    );

    const sendLambda = new lambda.DockerImageFunction(this, "sendLambda", {
      code: lambda.DockerImageCode.fromImageAsset("./src"),
    });

    botToken.grantRead(sendLambda);
  }
}

