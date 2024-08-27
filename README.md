# ECS Deployment Script

This project contains scripts to automate the deployment of an ECS service using AWS resources. The scripts are divided into multiple files for better manageability.

## Project Structure

- `main.py`: Contains the main execution logic.
- `config.py`: Contains configuration and environment variable fetching.
- `utils.py`: Contains utility functions for creating log groups, target groups, ECS services, and more.
- `start.sh`: A starter script to set environment variables, check and create ECR repository, push Docker image, and run the main script.
- `rollback.py`: A script to rollback the deployment by deleting ECS services, task definitions, target groups, ALB rules, and DNS records.
- `deployments/`: Directory where deployment information files are saved.

## Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. **Install dependencies:**
   Ensure you have `boto3` and `requests` installed. You can install them using pip:
   ```bash
   pip install boto3 requests
   ```

3. **Set up environment variables:**
   Make sure to set the following environment variables in your environment:
   - `AWS_REGION`
   - `VPC_ID`
   - `SUBNETS` (comma-separated)
   - `SECURITY_GROUPS` (comma-separated)
   - `ALB_ARN`
   - `PROJECT_NAME`
   - `ECR_REPO_URI`
   - `DOMAIN_NAME`
   - `ECS_CLUSTER`
   - `IMAGE_TAG`
   - `CLOUDFLARE_API_TOKEN`
   - `CLOUDFLARE_ZONE_ID`
   - `ALB_DNS_NAME`

4. **Run the starter script:**
   Execute the starter script to set environment variables, check and create ECR repository, push Docker image, and run the main script:
   ```bash
   ./start.sh
   ```

## Files Description

### `main.py`
This file contains the main execution logic. It orchestrates the creation of log groups, target groups, ECS services, and saves deployment information with a unique name. It also creates a CNAME record in Cloudflare.

### `config.py`
This file fetches and stores configuration values from environment variables.

### `utils.py`
This file contains utility functions:
- `create_log_group(log_group)`: Creates a CloudWatch log group.
- `create_target_group()`: Creates an ALB target group.
- `get_next_priority(listener_arn)`: Determines the next priority for ALB rules.
- `create_rule(listener_arn, target_group_arn, domain_name, rules_list)`: Creates an ALB rule.
- `register_task_definition()`: Registers an ECS task definition.
- `create_ecs_service(task_definition_arn, target_group_arn)`: Creates an ECS service.
- `save_deployment_info(task_definition_arn, target_group_arn, listener_arn, rules_list, timestamp)`: Saves deployment information to a JSON file in the `deployments` directory, including the project name in the file name.
- `create_cname_record_cloudflare(api_token, zone_id, domain_name, target)`: Creates a CNAME record in Cloudflare.

### `start.sh`
This file sets environment variables, checks and creates an ECR repository if necessary, pushes the Docker image to ECR, and runs the main script.

### `rollback.py`
This file contains functions to rollback the deployment:
- `load_deployment_info(file_path)`: Loads deployment information from a JSON file.
- `delete_ecs_service(cluster, service)`: Deletes an ECS service.
- `deregister_task_definition(task_definition_arn)`: Deregisters an ECS task definition.
- `delete_target_group(target_group_arn)`: Deletes an ALB target group.
- `delete_alb_rules(rules_list)`: Deletes ALB rules.
- `delete_cname_record_cloudflare(api_token, zone_id, domain_name)`: Deletes a CNAME record in Cloudflare.

To rollback a specific deployment, run:
```bash
python rollback.py <deployment_info_file>
```

## Logging
The scripts use Python's built-in logging module to log information and errors. Logs are configured to display at the `INFO` level.

## Contributing
Feel free to open issues or submit pull requests if you have any improvements or bug fixes.

## License
This project is licensed under the MIT License.