# Secret Santa Bot 🎁
This is a slack bot implementation of the classic game
[secret santa](https://en.wikipedia.org/wiki/Secret_Santa) using AWS lambdas and AWS cdk. 

## How it works
Once set up, the bot will send message to a slack channel of your choice
![Slack bot start message](/img/start_message.png)

Based who has reacted to the messages, it will collect the list of willing participants and send them a private message with the person who they will be giving a secret gift to. 
![Slack bot santa message](/img/santa_message.png)

## Technical Details
The app is made using several AWS lambda functions chained together using 
a step function and a message queue to send the secret santa assignment messages.
![Slack bot architecture](/img/diagram.png)

## Deploy the app on yourself
### Slack Bot Token
You need to set up an OAuth token for your bot. You will need to give the token the scopes: `chat:write`, `im:write`, `reactions:read`.
Then you need to install the bot to your workspace and invite the bot to the channel the bot will post into.

### Store your token in AWS secrets manager
The cdk stack expects the token to be stored as a secret in AWS secret manager. Store the OAuth token with the key as 'token'. Then make sure you put the name and region of your secret in our stack config

### Deploy the bot
The stack is deployed using the aws cdk, so you need to have `nodejs` and `npm` installed, then to install of required packages run
```
npm install .
```
To deploy the stack, run
```
cdk deploy
```



The `cdk.json` file tells the CDK Toolkit how to execute your app.

## Useful commands

 * `npm run build`   compile typescript to js
 * `npm run watch`   watch for changes and compile
 * `npm run test`    perform the jest unit tests
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk synth`       emits the synthesized CloudFormation template
