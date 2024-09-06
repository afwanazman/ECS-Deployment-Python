import json
import os
import boto3
import sys
from datetime import datetime

VALID_VCPUS = ['256', '512', '1024', '2048', '4096']  # in CPU shares (0.25, 0.5, 1, 2, 4 vCPUs)
VALID_MEMORY = ['512', '1024', '2048', '4096', '8192']  # in MiB

def update_deployment_info(task_definition_arn, target_group_arn, listener_arn, rules_list, project_name):
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        deployments_dir = os.path.join(script_dir, 'deployments')
        os.makedirs(deployments_dir, exist_ok=True)

        # Generate timestamp
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        file_name = os.path.join(deployments_dir, f'deployment_info_{project_name}_{timestamp}.json')

        # Remove old deployment files
        for file in os.listdir(deployments_dir):
            if file.startswith(f'deployment_info_{project_name}_'):
                os.remove(os.path.join(deployments_dir, file))

        # Save new deployment info
        with open(file_name, 'w') as f:
            json.dump({
                'ecs_cluster': ecs_cluster,
                'service_name': project_name,
                'task_definition_arn': task_definition_arn,
                'target_group_arn': target_group_arn,
                'listener_arn': listener_arn,
                'rules': rules_list,
                'domain_name': domain_name,
                'cloudflare_api_token': cloudflare_api_token,
                'cloudflare_zone_id': cloudflare_zone_id,
                'alb_dns_name': alb_dns_name
            }, f, indent=4, sort_keys=True)

        print(f"Deployment information updated and saved to {file_name}")
    except Exception as e:
        print(f"Error updating deployment info: {e}")

def main(json_file):
    # Initialize ECS client
    ecs_client = boto3.client('ecs', region_name='ap-southeast-5')

    # Load deployment info from provided JSON file
    with open(json_file, 'r') as file:
        deployment_info = json.load(file)

    # Extract data from JSON
    cluster_name = deployment_info['ecs_cluster']
    service_name = deployment_info['service_name']
    task_definition_arn = deployment_info['task_definition_arn']
    ecr_image_uri = deployment_info['task_definition_arn'].split('/')[1].split(':')[0]  # Extract ECR name from ARN

    # Prompt for new image tag
    new_image_tag = input("Enter the new image tag (e.g., v2.0): ")
    new_image_uri = f"{ecr_image_uri}:{new_image_tag}"

    # Prompt for vCPU and memory with validation
    cpu = input("Enter the vCPU value (e.g., 256 for 0.25 vCPU): ")
    while cpu not in VALID_VCPUS:
        print(f"Invalid vCPU value. Please enter one of the following: {', '.join(VALID_VCPUS)}")
        cpu = input("Enter the vCPU value (e.g., 256 for 0.25 vCPU): ")

    memory = input("Enter the memory value in MiB (e.g., 512 for 512 MiB): ")
    while memory not in VALID_MEMORY:
        print(f"Invalid memory value. Please enter one of the following: {', '.join(VALID_MEMORY)}")
        memory = input("Enter the memory value in MiB (e.g., 512 for 512 MiB): ")

    # Describe the current task definition to get the existing settings
    task_definition_desc = ecs_client.describe_task_definition(taskDefinition=task_definition_arn)
    container_definitions = task_definition_desc['taskDefinition']['containerDefinitions']

    # Update image URI in the container definitions
    for container in container_definitions:
        if container['name'] == 'your-container-name':  # Replace with your actual container name
            container['image'] = new_image_uri
            container['cpu'] = int(cpu)  # Update vCPU
            container['memory'] = int(memory)  # Update memory

    # Register the new task definition
    response = ecs_client.register_task_definition(
        family=task_definition_family,
        containerDefinitions=container_definitions,
        cpu=cpu,
        memory=memory,
        networkMode=network_mode,
        requiresCompatibilities=requires_compatibilities,
        taskRoleArn=task_role_arn,
        executionRoleArn=execution_role_arn,
        runtimePlatform=runtime_platform,
        tags=tags
    )

    # Extract new task definition ARN
    new_task_definition_arn = response['taskDefinition']['taskDefinitionArn']

    # Update ECS Service with new Task Definition
    update_response = ecs_client.update_service(
        cluster=cluster_name,
        service=service_name,
        taskDefinition=new_task_definition_arn
    )
    
    update_deployment_info(
        task_definition_arn=new_task_definition_arn,
        target_group_arn=deployment_info['target_group_arn'],
        listener_arn=deployment_info['listener_arn'],
        rules_list=deployment_info['rules'],
        project_name=service_name
    )

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python update_service.py <path_to_deployment_json>")
        sys.exit(1)

    json_file = sys.argv[1]
    main(json_file)

