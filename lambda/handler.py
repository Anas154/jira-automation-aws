import json
import os
import boto3
from botocore.exceptions import ClientError
import jira_simple

def lambda_handler(event, context):
    try:
        # Get secrets from AWS Secrets Manager
        region = os.environ.get('AWS_REGION', 'us-east-1')
        secret_name = "jira-automation-secrets"
        
        session = boto3.session.Session()
        client = session.client(service_name='secretsmanager', region_name=region)
        
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        secret = json.loads(get_secret_value_response['SecretString'])
        
        # Set environment variables
        os.environ['JIRA_BASE'] = secret['JIRA_BASE']
        os.environ['JIRA_LOGIN'] = secret['JIRA_LOGIN']
        os.environ['JIRA_API_TOKEN'] = secret['JIRA_API_TOKEN']
        os.environ['ACCOUNT_ID'] = secret['ACCOUNT_ID']
        
        # Call jira automation
        return jira_simple.lambda_handler(event, context)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {'statusCode': 500, 'body': f'Error: {str(e)}'}
