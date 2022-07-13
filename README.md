# CDK AWS Lambda Resource Sync Stack
 
This repo pulls specifically tagged AWS resource information from AWS ResourceGroupsTaggingAPI service and stores them in a DynamoDB table

## Features

* Recreates the DynamoDB and fetch the latest reources information from AWS ResourceGroupsTaggingAPI service
* Uses `EnvironmentName` as the primary key and `Owner` as the sort key for the resource items in DynamoDB

## Useful commands

 * `cdk bootstrap`   initialize assets before deploy
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region