# land.llandman

## Deployments Automation with GitHub Actions CI/CD Pipeline

The GitHub Actions CI/CD pipeline is composed of four Workflows:
* Publish Lambda Layer workflow: to deploy the python libraries that support both Real-Time and Batch data pipeline.
* Real-Time data pipeline workflow: deploys the infrastructure that supports the Real-Time data pipeline
* Batch data pipeline workflow: deploys the infrastructure that supports the Batch data pipeline
* Terraform Destroy workflow: that can be used to destroy the infrastructure of a given data pipeline

### Pre-requisites
Create the below IAM Roles in the new AWS `prod` account:
* gh-oidc-${env}-iam-role
* lambda-${env}-exec-role

From GitHub UI, create an environment (i.e- `prod`) then add the `IAM_ROLE_ARN` that the GitHub Actions CI/CD pipeline must assume to to deploy the infrastructure into the `prod` environment.


### Example of deploying the data pipelines into a new AWS Account (new env)
Let’s assume that you want to deploy the data pipelines into the production environment:

Step#1: Add a new job `prod-use1` into `lambda-layer.yml` workflow to publish the lambda layer

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

Step#2: Push your changes into the repo and make sure the new lambda layer had been created in the AWS account

Step#3: If everything is working as intended then merge your changes into the default branch `main`

**The lambda layer must be deployed first because it is required by the lambda functions that are used by the Real-Time and Batch data pipeline.

Step#4: Under `realtime` directory, clone `dev-use1` then rename the copied directory to `prod-use1`

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
 
Step#5: Add a new job `prod-use1` in Real-Time yaml workflow to deploy Real-Time data pipeline into `prod` AWS Account
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

Step#6: push your changes to deploy the infrastructure that supports the Real-Time data pipeline

Step#7: Under `batch` directory, clone `dev-use1` then rename the copied directory to `prod-use1`
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

Step#8: Add a new job `prod-use1` in Batch yaml workflow to deploy the Batch data pipeline into the `prod` AWS Account
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

Step#9: push your changes to deploy the infrastructure that supports the Batch data pipeline
