def get_create_date(ec2_client, launch_template_id):
    try:
        print("Fetching EC2 LaunchTemplate info")
        resp = ec2_client.describe_launch_template_versions(LaunchTemplateId=launch_template_id)
        laucn_template_data = resp["LaunchTemplateVersions"][0]
        return str(laucn_template_data["CreateTime"])
    except Exception as e:
        print(e)
        print('Error fetching  LaunchTemplate info from EC2.')
        raise e