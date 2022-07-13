from aws_cdk import (
    aws_lambda as _lambda,
    App, Stack
)


class LambdaResourceSyncStack(Stack):
    def __init__(self, app: App, id: str) -> None:
        super().__init__(app, id)

        # create lambda function
        function = _lambda.Function(self, "lambda_function",
                                    runtime=_lambda.Runtime.PYTHON_3_7,
                                    handler="main.handler",
                                    code=_lambda.Code.from_asset("lambda")
                                    )


app = App()
LambdaResourceSyncStack(app, "LambdaResourceSync")
app.synth()
