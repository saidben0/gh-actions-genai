data "aws_caller_identity" "this" {
  provider = aws.acc
}

data "aws_partition" "this" {
  provider = aws.acc
}

data "aws_region" "this" {
  provider = aws.acc
}

locals {
  account_id = data.aws_caller_identity.this.account_id
  partition  = data.aws_partition.this.partition
  region     = data.aws_region.this.name
}


data "aws_s3_bucket" "inputs_bucket" {
  provider = aws.acc
  bucket   = var.inputs_bucket_name
}

resource "random_id" "this" {
  byte_length = 6
  prefix      = "terraform-aws-"
}


resource "aws_sqs_queue" "dlq" {
  provider = aws.acc
  name     = "${var.prefix}-dlq"
  # kms_master_key_id = data.aws_kms_key.this.id
}


#########################################
############# LAMBDA LAYER ##############
#########################################
resource "null_resource" "lambda_layer" {
  provisioner "local-exec" {
    command = <<EOT
      pwd && ls
      cd ../module
      mkdir -p ./lambda-layer/python
      pip install -r ./lambda-layer/requirements.txt --platform=manylinux2014_x86_64 --only-binary=:all: -t ./lambda-layer/python
      # rm ./lambda-layer/requirements.txt
    EOT
  }

  triggers = {
    always_run = "${timestamp()}"
  }
  # triggers = {
  #   filebasesha = "${base64sha256(file("${path.module}/lambda-layer/requirements.txt"))}"
  # }
}

# Package the Lambda Layer
data "archive_file" "lambda_layer" {
  type        = "zip"
  output_path = "${path.module}/lambda-layer.zip"

  source_dir = "${path.module}/lambda-layer"
  excludes   = ["requirements.txt"]

  depends_on = [null_resource.lambda_layer]
}

# Create Lambda Layer
resource "aws_lambda_layer_version" "lambda_layer" {
  layer_name          = "python-libs"
  description         = "Lambda layer for Land Llandman doc processing"
  compatible_runtimes = ["python3.11"]
  filename            = data.archive_file.lambda_layer.output_path
  # filename            = "${path.module}/lambda-layer/python-libs.zip"
  source_code_hash = data.archive_file.lambda_layer.output_base64sha256
}

# Package the Lambda function code
data "archive_file" "this" {
  type        = "zip"
  source_dir  = "${path.module}/lambda/"
  excludes    = ["requirements.txt"]
  output_path = "${path.module}/outputs/queue-processing.zip"
}

resource "aws_lambda_function" "queue_processing_lambda_function" {
  provider                       = aws.acc
  filename                       = data.archive_file.this.output_path
  function_name                  = "${var.prefix}-${var.lambda_function_name}"
  role                           = aws_iam_role.queue_processing_lambda_role.arn
  layers                         = [aws_lambda_layer_version.lambda_layer.arn]
  handler                        = "lambda_handler.lambda_handler"
  source_code_hash               = data.archive_file.this.output_base64sha256
  runtime                        = "python3.11"
  timeout                        = "120"
  reserved_concurrent_executions = 100
  memory_size                    = 1024
  # kms_key_arn                    = data.aws_kms_key.this.arn

  environment {
    variables = {
      BUCKET_NAME       = var.inputs_bucket_name
      S3_URI            = "s3://${var.inputs_bucket_name}/tx/angelina/502d/502d1735-8162-4fed-b0a9-d12fcea75759.pdf"
      DDB_TABLE_NAME    = aws_dynamodb_table.model_outputs.name
      PROJECT_NAME      = var.project_name
      PROMPT_ID         = var.prompt_id
      PROMPT_VER        = var.prompt_ver
      SYSTEM_PROMPT_ID  = var.system_prompt_id
      SYSTEM_PROMPT_VER = var.system_prompt_ver
    }
  }

  tracing_config {
    mode = "Active"
  }
  dead_letter_config {
    target_arn = aws_sqs_queue.dlq.arn
  }

  # vpc_config {
  #   subnet_ids         = [module.vpc.private_subnets[0]]
  #   security_group_ids = [aws_security_group.allow_tls.id]
  # }

  depends_on = [aws_iam_role.queue_processing_lambda_role]
}
#########################################
#########################################
#########################################


resource "aws_sqs_queue" "this" {
  provider = aws.acc
  name     = "${var.prefix}-queue"
  # kms_master_key_id = data.aws_kms_key.this.id
  visibility_timeout_seconds = 120
  delay_seconds              = 90
  max_message_size           = 2048
  message_retention_seconds  = 86400
  receive_wait_time_seconds  = 10
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = 4
  })
}

# send an s3 event to sqs when new s3 object is created/uploaded
resource "aws_s3_bucket_notification" "sqs_notification" {
  provider = aws.acc
  bucket   = data.aws_s3_bucket.inputs_bucket.id

  queue {
    queue_arn = aws_sqs_queue.this.arn
    events    = ["s3:ObjectCreated:*"]
    # filter_prefix = aws_s3_object.inputs.key
    # filter_suffix = ".pdf"
  }

  depends_on = [aws_sqs_queue_policy.this]
}

# map sqs queue to trigger the lambda function when an 3 event is received
resource "aws_lambda_event_source_mapping" "this" {
  provider         = aws.acc
  event_source_arn = aws_sqs_queue.this.arn
  function_name    = aws_lambda_function.queue_processing_lambda_function.arn
  enabled          = true
  batch_size       = 10
}


resource "aws_dynamodb_table" "model_outputs" {
  provider     = aws.acc
  name         = "${var.prefix}-${var.dynamodb_table_name}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "document_id"
  range_key    = "chunk_id"

  attribute {
    name = "document_id"
    type = "S"
  }

  attribute {
    name = "chunk_id"
    type = "N"
  }

  point_in_time_recovery {
    enabled = true
  }

  # server_side_encryption {
  #   enabled     = true
  #   kms_key_arn = data.aws_kms_key.this.arn
  # }
}
