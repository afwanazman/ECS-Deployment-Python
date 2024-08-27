import os
from keys import access, secret, cloudflare_api_token

def get_env_variable(var_name):
    value = os.getenv(var_name)
    if value is None:
        raise EnvironmentError(f"Environment variable {var_name} is not set.")
    return value

aws_region = get_env_variable('AWS_REGION')
vpc_id = get_env_variable('VPC_ID')
subnets = get_env_variable('SUBNETS').split(',')
security_groups = get_env_variable('SECURITY_GROUPS').split(',')
alb_arn = get_env_variable('ALB_ARN')
project_name = get_env_variable('PROJECT_NAME')
repo_uri = get_env_variable("ECR_REPO_URI")
container_name = f'{project_name}-api-container'
task_family_name = f'{project_name}-api-task'
log_group = f'/ecs/container-logs'
domain_name = get_env_variable('DOMAIN_NAME')
ecs_cluster = get_env_variable('ECS_CLUSTER')
image_tag = get_env_variable('IMAGE_TAG')
task_role_arn = get_env_variable('TASK_ROLE_ARN')
execution_role_arn = get_env_variable('EXECUTION_ROLE_ARN')
cloudflare_zone_id = get_env_variable('CLOUDFLARE_ZONE_ID')
alb_dns_name = get_env_variable('ALB_DNS_NAME')
