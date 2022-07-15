import boto3
import ec2

partition_key = "EnvironmentName"
sort_key = "Creator"

TAG_KEY_CREATOR = "Creator"
TAG_KEY_NAME = "Name"
TAG_KEY_ENV_NAME = "Environment_name"
TAG_KEY_ENV_ID = "Environment_id"
TAG_KEY_ENV_TYPE = "Environment_type"
TAG_KEY_EXPIRATION = "Expiration"
TAG_KEY_OWNER = "Owner"
TAG_KEY_PRODUCT = "Product"
TAG_KEY_VERSION = "Version"
TAG_KEY_LAUNCHED_BY = "Launched_by"
TAG_VALUE_NO_CREATOR = "NoCreatorTag"


def recreate_table(dynamodb_client, table_name):
    """
    If DynamoDB `table_name` exists then drop it and then re-create
    """
    try:
        print(f"Re-creating DynamoDB table {table_name}")
        response = dynamodb_client.describe_table(TableName=table_name)

        dyn_resource = boto3.resource('dynamodb')

        if response:
            # delete table
            table = dyn_resource.Table(table_name)
            table.delete()
            print(f"Deleting {table.name}...")
            table.wait_until_not_exists()

        else:
            print(f"DynaoDB table: {table_name} doesn't exist!")

        # Now re-create table

        params = {
        'TableName': table_name,
        'KeySchema': [
            { 'AttributeName': 'EnvironmentName', 'KeyType': 'HASH'},
            {'AttributeName': 'Creator', 'KeyType': 'RANGE'}
        ],
        'AttributeDefinitions': [
            {'AttributeName': 'Creator', 'AttributeType': 'S'},
            {'AttributeName': 'EnvironmentName', 'AttributeType': 'S'}
        ],
        'BillingMode': 'PAY_PER_REQUEST'
        }
        table = dyn_resource.create_table(**params)
        print(f"Creating {table_name}...")
        table.wait_until_exists()
        return table    
    except Exception as e:
        print(e)
        print(f"Error re-creating DynamoDB table: {table_name}")
        raise e



def add_mpdk_env(dynamodb_client, ec2_client, mpdk_env, resources, dynamodb_table_name):
    firt_resource = resources[0]
    res_arn = firt_resource.get('ResourceARN')
    tags = firt_resource.get("Tags")
    creator = None
    for tag in tags:        
        if tag.get('Key') == TAG_KEY_CREATOR:
            creator = tag.get('Value')
            
    if not creator:
        print(f"ENV without Creator: {mpdk_env}")
        creator = TAG_VALUE_NO_CREATOR
            
    try:
        print(f"Fetching MPDK env from DynamoDB {mpdk_env}")
        response = dynamodb_client.get_item(
                    TableName=dynamodb_table_name,
                    Key={
                        "EnvironmentName": {"S": mpdk_env },
                        "Creator": {"S": creator }
                        }
                   )
        item = response["Item"]
        print(f"Got from DynamoDB: {item}")
        return False
    except KeyError:
        print(f"KeyError - Fetching MPDK env from DynamoDB {mpdk_env}")
        create_date_updated = False
        create_date = ""
        # add the mpdk_env to table 
        response =  dynamodb_client.put_item(
                        TableName=dynamodb_table_name,
                        Item={
                        "EnvironmentName": {"S": mpdk_env },
                        "Creator": {"S": creator },
                        "CreationDate": {"S": create_date},
                        "Cost.CurrentMonth": {"N": "0"},
                        "Cost.LastMonth": {"N": "0"},
                        "Cost.ProjectionMonthEnd": {"N":"0"}
                        }
                    )
        print(f"Put item to DynamoDB table: {mpdk_env} ")
        
        for res in resources:
            res_arn = res.get('ResourceARN')
            print(f"Adding res: {res_arn}")
            identifier = res_arn.split("/")[-1]
            [env_name, tag_name, env_id, env_type, expiration, owner, product, version, launched_by] = [str(x*0) for x in range(9) ]
            tags = res.get("Tags")
            #print(f"Tags: {tags}")
            for tag in tags:
                #print(f"Processing Tag: {tag} ") 
                if tag.get('Key') == TAG_KEY_ENV_NAME:
                    env_name = tag.get('Value', '') 
                # elif tag.get('Key') == TAG_KEY_CREATOR:
                #     creator = tag.get('Value', TAG_VALUE_NO_CREATOR)                
                elif tag.get('Key') == TAG_KEY_NAME:
                    tag_name = tag.get('Value', identifier) 
                elif tag.get('Key') == TAG_KEY_ENV_ID:
                    env_id = tag.get('Value', '')                
                elif tag.get('Key') == TAG_KEY_ENV_TYPE:
                    env_type = tag.get('Value', '')
                elif tag.get('Key') == TAG_KEY_EXPIRATION:
                    expiration = tag.get('Value', '')               
                elif tag.get('Key') == TAG_KEY_OWNER:
                    owner = tag.get('Value', '') 
                elif tag.get('Key') == TAG_KEY_PRODUCT:
                    product = tag.get('Value', '') 
                elif tag.get('Key') == TAG_KEY_VERSION:
                    version = tag.get('Value', '')  
                elif tag.get('Key') == TAG_KEY_LAUNCHED_BY:
                    launched_by = tag.get('Value', '')
                else:
                    print(f"Unprocessed tag: {tag}")

            service = res_arn.split(":")[2]
            type_tmp =  res_arn.split(":")[5]
            service_type = type_tmp.split('/')[0]
            if service_type == 'LaunchTemplate' and (not create_date_updated):
                create_date = ec2.get_create_date(ec2_client, identifier)
                create_date_updated = True
            region = res_arn.split(":")[3]
            # tags_count = len(tags)
            # add resource fields
            resource = "Resource" + "." + identifier
            response =  dynamodb_client.update_item(
                            TableName=dynamodb_table_name,
                            Key={
                                "EnvironmentName": {"S": mpdk_env },
                                 "Creator": {"S": creator }
                            },
                            AttributeUpdates={
                                "CreationDate": {
                                    'Value': { 'S': str(create_date) }
                                },
                                resource : {
                                    'Value': {
                                       'M': {
                                        "Identifier": {"S": identifier},
                                        "Region": {"S": region},
                                        "Service": {"S": service },
                                        "Type": {"S": service_type},
                                        "Tag.EnvironmentId": {"S": env_id },
                                        "Tag.EnvironmentType": {"S": env_type },
                                        "Tag.LaunchedBy": {"S": launched_by },
                                        "Tag.Name": {"S": tag_name },
                                        "Tag.Owner": {"S": owner},
                                        "Tag.Product": {"S": product},
                                        "Tag.Version": {"S": version },
                                        "Tag.Expiration": {"S": expiration }
                                     }
                                    }
                                }
                            }
                        )
            print(f"Updated resource {identifier} to DynamoDB ")
        return True
    except Exception as e:
        print(e)
        raise Exception(f"Fetching MPDK env from DynamoDB {env_name}")