import logging
import time
from utils import create_log_group, create_target_group, get_next_priority, create_rule, register_task_definition, create_ecs_service, create_cname_record_cloudflare, save_deployment_info, elbv2_client
from config import log_group, alb_arn, domain_name, cloudflare_api_token, cloudflare_zone_id, alb_dns_name

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    create_log_group(log_group)
    target_group_arn = create_target_group()
    if target_group_arn:
        listener_response = elbv2_client.describe_listeners(LoadBalancerArn=alb_arn)
        https_listener_arn = next(listener['ListenerArn'] for listener in listener_response['Listeners'] if listener['Port'] == 443)
        rules_list = []
        create_rule(https_listener_arn, target_group_arn, domain_name, rules_list)
        task_definition_arn = register_task_definition()
        if task_definition_arn:
            create_ecs_service(task_definition_arn, target_group_arn)
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            create_cname_record_cloudflare(cloudflare_api_token, cloudflare_zone_id, domain_name, alb_dns_name)
            save_deployment_info(task_definition_arn, target_group_arn, https_listener_arn, rules_list, timestamp)

if __name__ == "__main__":
    main()
