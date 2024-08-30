import logging
import time
import utils
import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    utils.create_log_group(config.log_group)
    target_group_arn = utils.create_target_group()
    if target_group_arn:
        listener_response = utils.elbv2_client.describe_listeners(LoadBalancerArn=config.alb_arn)
        https_listener_arn = next(listener['ListenerArn'] for listener in listener_response['Listeners'] if listener['Port'] == 443)
        rules_list = []
        utils.create_rule(https_listener_arn, target_group_arn, config.domain_name, rules_list)
        task_definition_arn = utils.register_task_definition()
        if task_definition_arn:
            utils.create_ecs_service(task_definition_arn, target_group_arn)
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            utils.create_cname_record_cloudflare(config.cloudflare_api_token, config.cloudflare_zone_id, config.domain_name, config.alb_dns_name)
            utils.save_deployment_info(task_definition_arn, target_group_arn, https_listener_arn, rules_list, timestamp)

if __name__ == "__main__":
    main()