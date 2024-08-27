#!/bin/bash
set -e

# Load environment variables from .env file
if [ -f .env ]; then
    source .env
else
    echo ".env file not found!"
    exit 1
fi

check_ecr_repo() {
    local repo_name="${PROJECT_NAME}"
    local ecr_repo_uri
    ecr_repo_uri=$(aws ecr describe-repositories --repository-names "${repo_name}" --region "${AWS_REGION}" --query 'repositories[0].repositoryUri' --output text 2>/dev/null)
    if [ "$ecr_repo_uri" == "None" ] || [ -z "$ecr_repo_uri" ]; then
        ecr_repo_uri=$(aws ecr create-repository --repository-name "${repo_name}" --region "${AWS_REGION}" --query 'repository.repositoryUri' --output text)
    fi
    ecr_repo_uri=$(echo "${ecr_repo_uri}" | xargs)
    echo "${ecr_repo_uri}"
}

aws ecr get-login-password --region "${AWS_REGION}" | docker login --username AWS --password-stdin 714443664516.dkr.ecr.ap-southeast-5.amazonaws.com

push_docker_image() {
    local ecr_repo_uri="$1"
    local tag="${IMAGE_TAG}"
    if [[ ! "${ecr_repo_uri}" =~ ^[a-zA-Z0-9._/-]+ ]]; then
        echo "Error: Invalid ECR repository URI."
        exit 1
    fi
    docker tag "${NEW_IMG}:latest" "${ecr_repo_uri}:${tag}"
    docker push "${ecr_repo_uri}:${tag}"
    if [ $? -ne 0 ]; then
        echo "Docker push failed."
        exit 1
    fi
}

ecr_repo_uri=$(check_ecr_repo)
export ECR_REPO_URI="${ecr_repo_uri}"
push_docker_image "${ecr_repo_uri}"
python main.py
