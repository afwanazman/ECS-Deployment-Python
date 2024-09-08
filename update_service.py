import json
import boto3
import sys
import re

VALID_VCPUS = ['256', '512', '1024', '2048', '4096']
VALID_MEMORY = ['512', '1024', '2048', '4096', '8192']

def find_existing_task_definition(ecs_client, family, cpu, memory, container_image):
    task_definitions = ecs_client.list_task_definitions(familyPrefix=family)
    for task_def_arn in reversed(task_definitions['taskDefinitionArns']):
        desc = ecs_client.describe_task_definition(taskDefinition=task_def_arn)
        container_defs = desc['taskDefinition']['containerDefinitions']
        for container in container_defs:
            if container['image'] == container_image:
                if str(container.get('cpu', '0')) == '0' and \
                   str(desc['taskDefinition'].get('cpu', '0')) == cpu and \
                   str(desc['taskDefinition'].get('memory', '0')) == memory:
                    return task_def_arn
    return None

def main(json_file):
    ecs_client = boto3.client('ecs', region_name='ap-southeast-5')

    with open(json_file, 'r') as file:
        deployment_info = json.load(file)

    cluster_name = deployment_info['ecs_cluster']
    service_name = deployment_info['service_name']
    task_definition_arn = deployment_info['task_definition_arn']

    # Fetch the current task definition
    current_task_def = ecs_client.describe_task_definition(taskDefinition=task_definition_arn)
    current_container_def = current_task_def['taskDefinition']['containerDefinitions'][0]

    # Extract the current image URI
    current_image_uri = current_container_def['image']

    # Use regex to split the image URI into its components
    match = re.match(r'(.*/)([^:]+)(:.*)?', current_image_uri)
    if match:
        ecr_repo_url = match.group(1)  # This includes the account ID and region
        image_name = match.group(2)
        current_tag = match.group(3)[1:] if match.group(3) else 'latest'
    else:
        print(f"Error: Unable to parse the current image URI: {current_image_uri}")
        sys.exit(1)

    print(f"Current image: {image_name}")
    print(f"Current tag: {current_tag}")

    new_image_tag = input(f"Enter the new image tag (current: {current_tag}): ")
    new_image_uri = f"{ecr_repo_url}{image_name}:{new_image_tag}"

    print(f"New image URI will be: {new_image_uri}")

    cpu = input("Enter the vCPU value (e.g., 256 for 0.25 vCPU): ")
    while cpu not in VALID_VCPUS:
        cpu = input("Invalid vCPU value. Enter one of the following: 256, 512, 1024, 2048, 4096: ")

    memory = input("Enter the memory value in MiB (e.g., 512 for 512 MiB): ")
    while memory not in VALID_MEMORY:
        memory = input("Invalid memory value. Enter one of the following: 512, 1024, 2048, 4096, 8192: ")

    family = current_task_def['taskDefinition']['family']
    network_mode = current_task_def['taskDefinition']['networkMode']
    requires_compatibilities = current_task_def['taskDefinition']['requiresCompatibilities']
    task_role_arn = current_task_def['taskDefinition'].get('taskRoleArn', '')
    execution_role_arn = current_task_def['taskDefinition'].get('executionRoleArn', '')
    runtime_platform = current_task_def['taskDefinition'].get('runtimePlatform', {})

    existing_task_definition = find_existing_task_definition(ecs_client, family, cpu, memory, new_image_uri)

    if existing_task_definition:
        new_task_definition_arn = existing_task_definition
        print(f"Using existing task definition: {new_task_definition_arn}")
    else:
        response = ecs_client.register_task_definition(
            family=family,
            networkMode=network_mode,
            containerDefinitions=[{
                'name': current_container_def['name'],
                'image': new_image_uri,
                'cpu': 0,  # CPU at container level set to 0
                'portMappings': current_container_def.get('portMappings', []),
                'essential': current_container_def['essential'],
                'logConfiguration': current_container_def.get('logConfiguration', {}),
                'healthCheck': current_container_def.get('healthCheck', {})
            }],
            taskRoleArn=task_role_arn,
            executionRoleArn=execution_role_arn,
            requiresCompatibilities=requires_compatibilities,
            cpu=cpu,
            memory=memory,
            runtimePlatform=runtime_platform,
        )
        new_task_definition_arn = response['taskDefinition']['taskDefinitionArn']
        print(f"New task definition registered: {new_task_definition_arn}")

    ecs_client.update_service(
        cluster=cluster_name,
        service=service_name,
        taskDefinition=new_task_definition_arn
    )
    print(f"ECS Service updated successfully")

    # Update the deployment.json file with the new task definition ARN
    deployment_info['task_definition_arn'] = new_task_definition_arn
    with open(json_file, 'w') as file:
        json.dump(deployment_info, file, indent=4)
    print(f"Updated new task definition ARN: {new_task_definition_arn} to json")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python update_service.py <path_to_deployment_json>")
        sys.exit(1)

    json_file = sys.argv[1]
    main(json_file)
