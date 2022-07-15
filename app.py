from aws_cdk import (
    aws_lambda as _lambda,
    aws_iam as _iam,
    aws_dynamodb as _dynamodb,
    App, Stack
)

COST_REPORT_DDB_TABLE_NAME = "AWSCostOptimization"
PARTITION_KEY = "Creator"
SORT_KEY = "EnvironmentName"


class LambdaResourceSyncStack(Stack):
    def __init__(self, app: App, id: str) -> None:
        super().__init__(app, id)

        # Create dynamo table to hold resource info
        cost_opt_table = _dynamodb.Table(
            self, COST_REPORT_DDB_TABLE_NAME,
            partition_key=_dynamodb.Attribute(name=PARTITION_KEY, type=_dynamodb.AttributeType.STRING),
            sort_key=_dynamodb.Attribute(name=SORT_KEY, type=_dynamodb.AttributeType.STRING)
        )

        # Add iam policy document
        policy_document = """{
                            "Version": "2012-10-17",
                            "Statement": [{
                                "Sid": "Statement-01",
                                "Effect": "Allow",
                                "Action": ["ec2:Describe*",
                                           "tag:GetResources",
                                           "cloudformation:ListStackResources",
                                           "cloudformation:DescribeStacks",
                                           "logs:CreateLogGroup",
                                           "logs:CreateLogStream",
                                           "logs:PutLogEvents"
                                           ],
                                "Resource": "*"
                            }, {
                                "Sid": "Statement-02",
                                "Effect": "Allow",
                                "Action": ["dynamodb:BatchGetItem",
                                            "dynamodb:GetItem",
                                            "dynamodb:Query",
                                            "dynamodb:Scan",
                                            "dynamodb:BatchWriteItem",
                                            "dynamodb:PutItem",
                                            "dynamodb:UpdateItem",
                                            "dynamodb:DescribeTable",
                                            "dynamodb:CreateTable",
                                            "dynamodb:DeleteTable",
                                            ],
                                "Resource": cost_opt_table
                            }
                            ]
                        }"""

        custom_policy_document = _iam.PolicyDocument.from_json(policy_document)

        # Pass this document as an initial document to a ManagedPolicy
        managed_policy = _iam.ManagedPolicy(self, "ResSyncManagedPolicy",
            document=custom_policy_document
        )

        #Create role with the correct iam policy
        lambda_role = _iam.Role(scope=self, id='res-sync-lambda-exec-role',
                                assumed_by =_iam.ServicePrincipal('lambda.amazonaws.com'),
                                role_name='res-sync-lambda-exec-role',
                                managed_policies=[managed_policy,]
                                )
        

        # create lambda function
        function = _lambda.Function(self, "lambda_function",
                                    runtime=_lambda.Runtime.PYTHON_3_7,
                                    handler="lambda_function.lambda_handler",
                                    code=_lambda.Code.from_asset("./lambda/rgta-sync"),
                                    role=lambda_role,
                                    environment = { 
                                        COST_REPORT_DDB_TABLE_NAME : cost_opt_table
                                    }
                                    )


app = App()
LambdaResourceSyncStack(app, "LambdaResourceSync")
app.synth()
