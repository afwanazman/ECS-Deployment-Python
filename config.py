import os
from keys import access, secret, cloudflare_api_token

aws_region = os.getenv('AWS_REGION')
vpc_id = os.getenv('VPC_ID')
subnets = os.getenv('SUBNETS').split(',')
security_groups = os.getenv('SECURITY_GROUPS').split(',')
alb_arn = os.getenv('ALB_ARN')
project_name = os.getenv('PROJECT_NAME')
repo_uri = os.getenv("ECR_REPO_URI")
container_name = f'{project_name}-api-container'
task_family_name = f'{project_name}-api-task'
log_group = f'/ecs/container-logs'
domain_name = os.getenv('DOMAIN_NAME')
ecs_cluster = os.getenv('ECS_CLUSTER')
image_tag = os.getenv('IMAGE_TAG')
task_role_arn = os.getenv('TASK_ROLE_ARN')
execution_role_arn = os.getenv('EXECUTION_ROLE_ARN')
cloudflare_zone_id = os.getenv('CLOUDFLARE_ZONE_ID')
alb_dns_name = os.getenv('ALB_DNS_NAME')
