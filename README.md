# land.llandman

## Deployments Automation with GitHub Actions CI/CD Pipeline

The GitHub Actions CI/CD pipeline for this project consists of four separate workflows:

1. Publish Lambda Layer Workflow: this workflow is responsible for deploying the Python libraries that support both the Real-Time and Batch data pipelines.

2. Real-Time Data Pipeline Workflow: this workflow deploys the infrastructure required to support the Real-Time data pipeline.

3. Batch Data Pipeline Workflow: this workflow deploys the infrastructure required to support the Batch data pipeline. 

4. Terraform Destroy Workflow: this workflow can be used to destroy the infrastructure of a given data pipeline, whether that's the Real-Time or Batch pipeline.

The pipeline uses these four distinct workflows to manage the deployment and management of the different components that make up the overall data pipeline system.


## Deploy the data pipelines into a new AWS Account Environment (`prod`)
The best way to explain how to deploy the data pipelines into a new environment is by example.

Let’s assume that you want to deploy the data pipelines into the production environment.
### Pre-requisites
- Create the below IAM Roles in the new AWS `prod` account:
  - `gh-oidc-${env}-iam-role`: assumed by the GitHub Actions CI/CD pipeline to deploy into the new AWS environment
  - `lambda-${env}-exec-role`: assumed by the AWS Lambda functions that are deployed as part of the data pipelines infrastructure. 

- From GitHub UI:
  - Create the new environment that you want to deploy into (i.e- `prod`)
  - Add the `IAM_ROLE_ARN` that the GitHub Actions CI/CD pipeline must assume to deploy the infrastructure into the new AWS environment (i.e- `prod`).


#### Step#1: Publish the lambda layer
This lambda layer contains the python libraries that are shared across the lambda functions of this solution.

- Add a new job `prod-use1` into `lambda-layer.yml` workflow:
```yaml
name: Lambda Layer Pipeline

on:
  push:
    branches:
      - dev
    paths:
      - 'lambda-layer/requirements.txt'

defaults:
  run:
    shell: bash

jobs:
  dev-use1:
    uses: ./.github/workflows/publish-layer.yml
    with:
      env: dev
      aws-region: us-east-1
   
  prod-use1:
   uses: ./.github/workflows/publish-layer.yml
   with:
     env: prod
     aws-region: us-east-1
```

- Update `lambda-layer/requirements.txt` file
`Lambda Layer Pipeline` runs when `lambda-layer/requirements.txt` is updated.
You can just add a whitespace to the end of the file abd that should the `Lambda Layer Pipeline` to run an deploy the lambda layer into the AWS environment.

- Push your changes into the repo and make sure the new lambda layer had been created in the new AWS account/env
The lambda layer must be deployed first because it is required by the lambda functions that are used by the Real-Time and Batch data pipeline.

- Merge your changes into the default branch `main`


#### Step#2: Deploy Real-Time Data Pipeline
Adding a new job to deploy the Real-Time data pipeline to the new AWS environment.

- Under `realtime` directory, clone `dev-use1` then rename the copied directory to `prod-use1`

In `prod-dev1` directory, update `backend.tf` and `providers.tf` accordingly so that it uses the correct backend and the correct aws providers:

```bash
# backend.tf
terraform {
  backend "s3" {
    bucket = "di-prod-terraform"
    key    = "prod/llandman/terraform.tfstate"
    region = "us-east-1"
  }
}

# providers.tf
provider "aws" {
  alias  = "use1"
  region = "us-east-1"

  default_tags {
    tags = {
      Team         = "Tech-Land-Manufacturing@enverus.com"
      Dataset      = "land"
      SourceCode   = "https://github.com/enverus-ea/land.llandman"
      Component    = "llandman"
      BusinessUnit = "ea"
      Product      = "courthouse"
      Environment  = "prod"
    }
  }
}

provider "awscc" {
  alias  = "use1"
  region = "us-east-1"
}
```

- Add a new job `prod-use1` in Real-Time yaml workflow to deploy Real-Time data pipeline into `prod` AWS Account
```yaml
name: Real-Time Pipeline

on:
  push:
    branches:
      - dev
    paths:
      - 'realtime/**'
  workflow_run:
    workflows: ["Lambda Layer Pipeline"]
    branches: [dev]
    types:
      - completed

jobs:
  dev-use1:
    if: github.event_name == 'push' || ${{ github.event.workflow_run.outputs.env == 'dev' }}
    uses: ./.github/workflows/tfapply.yml
    with:
      data-pipeline: realtime
      env: dev
      aws-env-dir: dev-use1
      aws-region: us-east-1
      lambda-role-name: llandman-dev-lambda-exec-role
      deploy: 'true'

  prod-use1:
   if: github.event_name == 'push' || ${{ github.event.workflow_run.outputs.env == 'prod' }}
   uses: ./.github/workflows/tfapply.yml
   with:
     data-pipeline: realtime
     env: prod
     aws-env-dir: prod-use1
     aws-region: us-east-1
     lambda-role-name: llandman-prod-lambda-exec-role
     deploy: 'true'
```

- Push your changes to deploy the infrastructure that supports the Real-Time data pipeline

#### Step#3: Deploy Batch Data Pipeline
Adding a new job to deploy the Batch data pipeline to the new AWS environment.

- Under `batch` directory, clone `dev-use1` then rename the copied directory to `prod-use1`
In `prod-dev1` directory, update `backend.tf` and `providers.tf` accordingly so that it uses the correct backend and the correct aws providers:

```bash
# backend.tf
terraform {
  backend "s3" {
    bucket = "di-prod-terraform"
    key    = "prod/llandman/terraform.batch.tfstate"
    region = "us-east-1"
  }
}

# providers.tf
provider "aws" {
  alias  = "use1"
  region = "us-east-1"

  default_tags {
    tags = {
      Team         = "Tech-Land-Manufacturing@enverus.com"
      Dataset      = "land"
      SourceCode   = "https://github.com/enverus-ea/land.llandman"
      Component    = "llandman"
      BusinessUnit = "ea"
      Product      = "courthouse"
      Environment  = "prod"
    }
  }
}

provider "awscc" {
  alias  = "use1"
  region = "us-east-1"
}
```

- Add a new job `prod-use1` in Batch yaml workflow to deploy the Batch data pipeline into the `prod` AWS Account
```yaml
name: Batch Pipeline

on:
  push:
    branches:
      - dev
    paths:
      - 'batch/**'
  workflow_run:
    workflows: ["Lambda Layer Pipeline"]
    branches: [dev]
    types:
      - completed

jobs:
  dev-use1:
    if: github.event_name == 'push' || ${{ github.event.workflow_run.outputs.env == 'dev' }}
    uses: ./.github/workflows/tfapply.yml
    with:
      data-pipeline: batch
      env: dev
      aws-env-dir: dev-use1
      aws-region: us-east-1
      lambda-role-name: llandman-dev-lambda-exec-role
      deploy: 'true'

  prod-use1:
   if: github.event_name == 'push' || ${{ github.event.workflow_run.outputs.env == 'prod' }}
   uses: ./.github/workflows/tfapply.yml
   with:
     data-pipeline: batch
     env: prod
     aws-env-dir: prod-use1
     aws-region: us-east-1
     lambda-role-name: llandman-prod-lambda-exec-role
     deploy: 'true'
```

- Push your changes to deploy the infrastructure that supports the Batch data pipeline


## `Terraform Destroy` workflow
The `terraform destroy` workflow is configured to run manually to prevent accidental destruction of the infrastructure that supports the data pipelines.

If `terraform destroy` is needed to be executed then the user needs to select the `Terraform Destroy` workflow from the GitHub Actions UI then enter the required workflow inputs before it can be executed.
```yaml
    inputs:
      env:
        description: 'deployment environment'
        required: true
        default: 'dev'
        type: choice
        options:
          - dev
          - prod
      data-pipeline:
        required: true
        default: 'batch'
        type: choice
        options:
          - 'batch'
          - 'realtime'
      aws-env-dir:
        required: true
        default: 'dev-use1'
        type: choice
        options:
          - 'dev-use1'
          - 'dev-usw2'
      aws-region:
        required: true
        default: 'us-east-1'
        type: choice
        options:
          - 'us-east-1'
          - 'us-west-2'
      lambda-role-name:
        required: true
        default: 'llandman-dev-lambda-exec-role'
        type: string
```
