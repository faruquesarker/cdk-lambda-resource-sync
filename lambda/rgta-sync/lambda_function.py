import os
import logging
import json
import boto3

import resource_groups_tagging_api as rgta
import dynamodb

LOG = logging.getLogger()
LOG.setLevel(logging.INFO)

LOG.info('Loading Lambda function rgta_sync...')

rgta_client = boto3.client('resourcegroupstaggingapi')

ec2_client = boto3.client('ec2')

dynamodb_client = boto3.client('dynamodb')
COST_REPORT_DDB_TABLE_NAME = os.environ.get("COST_REPORT_DDB_TABLE_NAME")

def lambda_handler(event, context):
    res_envs = rgta.get_tag_values(rgta_client)
    LOG.info("Resource envs: " + json.dumps(res_envs))
    
    if False:
        #Drop and re-create DynamoDB table
        table = dynamodb.recreate_table(dynamodb_client, COST_REPORT_DDB_TABLE_NAME)

        if not table:
            return {
            'statusCode': 404,
            'body': json.dumps('Failed to re-create DynamoDB table!')
        }

        # Update DynamoDB Table
        for res_env in res_envs:
            resources = rgta.get_resources(rgta_client, res_env)
            LOG.info("Resources: " + json.dumps(resources))
            added_to_table = dynamodb.add_res_env(dynamodb_client, ec2_client, res_env, resources, COST_REPORT_DDB_TABLE_NAME)
            if added_to_table:
                LOG.info("MS360 Env : " + res_env + " sync'd to DynamoDB table: " + str(len(resources)))
    return {
        'statusCode': 200,
        'body': json.dumps('Success running Lambda RGTA Sync To DynamoDB!')
    }

