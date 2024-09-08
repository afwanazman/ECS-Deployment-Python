import os
import boto3
import docker

# Load environment variables from .env file
def load_env_variables():
    with open('.env', 'r') as f:
        for line in f:
            key, value = line.strip().split('=')
            os.environ[key.strip()] = value.strip()

load_env_variables()

# Define AWS region and ECR client
AWS_REGION = os.environ['AWS_REGION']
ecr = boto3.client('ecr', region_name=AWS_REGION)

# Check if ECR repository exists, create if not
def check_ecr_repo():
    repo_name = os.environ['PROJECT_NAME']
    try:
        response = ecr.describe_repositories(repositoryNames=[repo_name])
        ecr_repo_uri = response['repositories'][0]['repositoryUri']
    except ecr.exceptions.RepositoryNotFoundException:
        response = ecr.create_repository(repositoryName=repo_name)
        ecr_repo_uri = response['repository']['repositoryUri']
    return ecr_repo_uri

# Get ECR repository URI
ecr_repo_uri = check_ecr_repo()

# Login to ECR
password = ecr.get_authorization_token(registryIds=['714443664516'])['authorizationToken']
docker_client = docker.from_env()
docker_client.login(username='AWS', password=password, registry='https://' + ecr_repo_uri)

# Push Docker image to ECR
def push_docker_image(ecr_repo_uri):
    image_tag = os.environ['IMAGE_TAG']
    new_img = 'NEW_IMG'  # Replace with the actual image name
    docker_client.tag(new_img, ecr_repo_uri + ':' + image_tag)
    docker_client.push(ecr_repo_uri + ':' + image_tag)

push_docker_image(ecr_repo_uri)

# Run Python script
import main
