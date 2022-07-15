from distutils import core
from aws_cdk import (
    aws_lambda as _lambda,
    aws_iam as _iam,
    aws_dynamodb as _dynamodb,
    aws_logs as _logs,
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

        # Add iam policy
        policy_statement = _iam.PolicyStatement( 
                                actions=["ec2:Describe*",
                                        "tag:GetResources",
                                        "tag:GetTagValues",
                                        "cloudformation:ListStackResources",
                                        "cloudformation:DescribeStacks",
                                        "logs:CreateLogGroup",
                                        "logs:CreateLogStream",
                                        "logs:PutLogEvents"
                                        ],
                                resources=["*"]
                            )

        #Create role with the correct iam policy
        lambda_role = _iam.Role(scope=self, id='res-sync-lambda-exec-role',
                                assumed_by =_iam.ServicePrincipal('lambda.amazonaws.com'),
                                role_name='res-sync-lambda-exec-role'
                                )
        lambda_role.add_to_policy(policy_statement)
        
        # create lambda function
        lambda_function = _lambda.Function(self, "lambda_function",
                                    runtime=_lambda.Runtime.PYTHON_3_7,
                                    handler="lambda_function.lambda_handler",
                                    code=_lambda.Code.from_asset("./lambda/rgta-sync"),
                                    timeout= core.Duration.seconds(900),
                                    role=lambda_role,
                                    log_retention=_logs.RetentionDays.ONE_DAY,
                                    environment = { 
                                        "COST_REPORT_DDB_TABLE_NAME" : cost_opt_table.table_name
                                    }
                                    )
        cost_opt_table.grant_full_access(lambda_function)


app = App()
LambdaResourceSyncStack(app, "LambdaResourceSync")
app.synth()
