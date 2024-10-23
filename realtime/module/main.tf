data "aws_caller_identity" "this" {
  provider = aws.acc
}

data "aws_partition" "this" {
  provider = aws.acc
}

data "aws_region" "this" {
  provider = aws.acc
}


data "aws_s3_bucket" "inputs_bucket" {
  provider = aws.acc
  bucket   = var.inputs_bucket_name
}

data "aws_iam_role" "llandman_lambda_exec_role" {
  provider = aws.acc
  name     = "${var.prefix}-${var.env}-lambda-exec-role"
}

resource "random_id" "this" {
  byte_length = 6
  prefix      = "terraform-aws-"
}


resource "aws_sqs_queue" "redrive_dlq" {
  provider   = aws.acc
  name       = "${var.prefix}-${var.env}-redrive-dlq.fifo"
  fifo_queue = true
}


# lambda code signing
resource "aws_signer_signing_profile" "this" {
  name        = var.prefix
  platform_id = "AWSLambda-SHA384-ECDSA"
  signature_validity_period {
    value = 3
    type  = "MONTHS"
  }
}

resource "aws_lambda_code_signing_config" "this" {
  allowed_publishers {
    signing_profile_version_arns = [aws_signer_signing_profile.this.version_arn]
  }
  policies {
    untrusted_artifact_on_deployment = "Warn"
  }
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
  function_name                  = "${var.prefix}-${var.env}-queue-processing"
  role                           = data.aws_iam_role.llandman_lambda_exec_role.arn
  layers                         = [var.lambda_layer_version_arn]
  handler                        = "lambda_handler.lambda_handler"
  source_code_hash               = data.archive_file.this.output_base64sha256
  runtime                        = "python${var.python_version}"
  timeout                        = "900"
  reserved_concurrent_executions = 100
  memory_size                    = 1024

  environment {
    variables = {
      DDB_TABLE_NAME = aws_dynamodb_table.model_outputs.name
      QUEUE_URL      = aws_sqs_queue.this.url
      TAGS           = jsonencode(var.tags)
    }
  }
  code_signing_config_arn = aws_lambda_code_signing_config.this.arn

  tracing_config {
    mode = "Active"
  }
}


resource "aws_sqs_queue" "this" {
  provider                    = aws.acc
  name                        = "${var.prefix}-${var.env}-queue.fifo"
  visibility_timeout_seconds  = 900
  delay_seconds               = 0
  max_message_size            = 10000
  message_retention_seconds   = 864000
  receive_wait_time_seconds   = 10
  fifo_queue                  = true
  content_based_deduplication = true
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.redrive_dlq.arn
    maxReceiveCount     = 4
  })
}

# Define an sqs policy to allow S3 to send messages to the SQS queue
resource "aws_sqs_queue_policy" "this" {
  provider  = aws.acc
  queue_url = aws_sqs_queue.this.url

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = {
          Service = "s3.amazonaws.com"
        },
        Action   = "sqs:SendMessage",
        Resource = aws_sqs_queue.this.arn,
        Condition = {
          ArnEquals = {
            "aws:SourceArn" = data.aws_s3_bucket.inputs_bucket.arn
          }
        }
      }
    ]
  })
}

# map sqs queue to trigger the lambda function when an 3 event is received
resource "aws_lambda_event_source_mapping" "this" {
  provider         = aws.acc
  event_source_arn = aws_sqs_queue.this.arn
  function_name    = aws_lambda_function.queue_processing_lambda_function.arn
  enabled          = true
  batch_size       = 1
}


resource "aws_dynamodb_table" "model_outputs" {
  provider = aws.acc
  # name         = "${var.prefix}-${var.env}-model-outputs"
  name         = "${var.prefix}-model-outputs"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "document_id"
  range_key    = "ingestion_time"

  attribute {
    name = "document_id"
    type = "S"
  }

  attribute {
    name = "ingestion_time"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  # prevent destruction of this table
  lifecycle {
    prevent_destroy = true
  }
}





# resource "null_resource" "lambda_layer" {
#   provisioner "local-exec" {
#     command = <<EOT
#       pwd && ls
#       cd ../module
#       mkdir -p ./lambda-layer/python
#       pip install -r ./lambda-layer/requirements.txt --platform=manylinux2014_x86_64 --only-binary=:all: -t ./lambda-layer/python
#       # rm ./lambda-layer/requirements.txt
#     EOT
#   }

#   triggers = {
#     filebasesha = "${base64sha256(file("${path.module}/lambda-layer/requirements.txt"))}"
#   }
#   # triggers = {
#   #   always_run = "${timestamp()}"
#   # }
# }

# # Package the Lambda Layer
# data "archive_file" "lambda_layer" {
#   type        = "zip"
#   output_path = "${path.module}/lambda-layer.zip"

#   source_dir = "${path.module}/lambda-layer"
#   excludes   = ["requirements.txt"]

#   depends_on = [null_resource.lambda_layer]
# }

# # Create Lambda Layer
# resource "aws_lambda_layer_version" "lambda_layer" {
#   layer_name          = "python-libs"
#   description         = "Lambda layer for Land Llandman doc processing"
#   compatible_runtimes = ["python${var.python_version}"]
#   filename            = data.archive_file.lambda_layer.output_path
#   source_code_hash    = data.archive_file.lambda_layer.output_base64sha256
# }



# # send an s3 event to sqs when new s3 object is created/uploaded
# resource "aws_s3_bucket_notification" "sqs_notification" {
#   provider = aws.acc
#   bucket   = data.aws_s3_bucket.inputs_bucket.id

#   queue {
#     queue_arn = aws_sqs_queue.this.arn
#     events    = ["s3:ObjectCreated:*"]
#     # filter_prefix = aws_s3_object.inputs.key
#     # filter_suffix = ".pdf"
#   }

#   depends_on = [aws_sqs_queue_policy.this]
# }
