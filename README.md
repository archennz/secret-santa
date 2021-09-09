# Secret Santa Bot 🎁

This is a slack bot implementation of the classic game
[secret santa](https://en.wikipedia.org/wiki/Secret_Santa) using AWS lambdas and AWS cdk.

## How it works

Once triggered, the bot will send message to a slack channel of your choice

<img src="/img/start_message.png" alt="Slack bot start message" width="400"/>

After one week, based who has reacted to the messages,
it collects the list of participants and send them a private message with the person who they will be giving a secret gift to.

<img src="/img/santa_message.png" alt="Slack bot start message" width="400"/>

If less than two participants have reacted, then it will notify the channel that secret santa will not commence.

## Technical Details
The app is made using several AWS lambda functions chained together using
a step function and a message queue to send the secret santa assignment messages.

![Slack bot architecture](/img/diagram.png)

* The step function manages sending out the first welcome message as well as depositing assigned gift pairs each into the SQS queue.
Once its done, it messages the slack channel confirming that pairing has been completed.
* The send lambda prompt lambda polls the queue to send the private messages informing the gift-giver their recipients.
Exponential back-off is used to avoid rate limiting.
If gift pairs failed to send even after retry, it will be redirected to the dead line queue triggering a cloudwatch alarm.

## Deploy the app on yourself

### Slack Bot Token

You need to set up an OAuth token for your bot. You will need to give the token the scopes: `chat:write`, `im:write`, `reactions:read`.
Then you need to install the bot to your workspace and invite the bot to your slack channel.

### Store your token in AWS secrets manager

The cdk stack expects the token to be stored as a secret in AWS secret manager. Store the OAuth token with the key as 'token'. Then make sure you put the name and region of your secret in our stack config.

### Configure the bot

You need to set:

* botTokenName: name of the AWS secrets for bot token
* secretRegion: region of the bot secret
* channelID: the slack channel you wish the bot to post in

Optional:
waitTime: time waiting for users to opt in to secret santa

### Deploy the bot on AWS

The stack is deployed using the aws cdk, so you need to have `nodejs` and `npm` installed, then to install of required packages run
```
npm install .
```
To deploy the stack, run
```
cdk deploy
```

The `cdk.json` file tells the CDK Toolkit how to execute your app.

### Useful cdk commands

 * `npm run build`   compile typescript to js
 * `npm run watch`   watch for changes and compile
 * `npm run test`    perform the jest unit tests
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk synth`       emits the synthesized CloudFormation template
