data "aws_iam_role" "llandman_sfn_exec_role" {
  provider = aws.acc
  name     = "${var.prefix}-${var.env}-sfn-exec-role"
}

data "aws_iam_role" "llandman_event_exec_role" {
  provider = aws.acc
  name     = "${var.prefix}-${var.env}-event-exec-role"
}

resource "aws_cloudwatch_log_group" "sfn_cw_log_group" {
  provider          = aws.acc
  name_prefix       = "/aws/vendedlogs/states/"
  retention_in_days = 365
}

resource "aws_sfn_state_machine" "inference_sfn" {
  provider   = aws.acc
  name       = "${var.prefix}-${var.env}-inference-sfn"
  role_arn   = data.aws_iam_role.llandman_sfn_exec_role.arn
  definition = file("${path.module}/templates/inference-statemachine.asl.json")
  logging_configuration {
    log_destination        = "${aws_cloudwatch_log_group.sfn_cw_log_group.arn}:*"
    include_execution_data = true
    level                  = "ALL"
  }

  tracing_configuration {
    enabled = true
  }
}

# create an event rule
resource "aws_cloudwatch_event_rule" "inference_sfn_rule" {
  provider    = aws.acc
  name        = "${var.prefix}-${var.env}-inference-sfn-rule"
  description = "Trigger Step Function"

  event_pattern = <<EOF
{
  "source": ["aws.s3"],
  "detail-type": ["Object Created"],
  "detail": {
    "bucket": {
      "name": ["${aws_s3_bucket.this.id}"]
    },
    "object": {
      "key": [{"prefix": "${aws_s3_object.inputs.key}"}]
    }
  }
}
EOF
}

# define the step function as the target for the eventbridge rule
resource "aws_cloudwatch_event_target" "sfn_inference_target" {
  provider = aws.acc
  rule     = aws_cloudwatch_event_rule.inference_sfn_rule.name
  arn      = aws_sfn_state_machine.inference_sfn.arn
  role_arn   = data.aws_iam_role.llandman_event_exec_role.arn
}




# # create an eventbridge role
# resource "aws_iam_role" "llandman_event_exec_role" {
#   provider    = aws.acc
#   name_prefix = "${var.prefix}-${var.env}-event-exec-role"
#   assume_role_policy = jsonencode({
#     Version = "2012-10-17"
#     Statement = [
#       {
#         Action = "sts:AssumeRole"
#         Effect = "Allow"
#         Principal = {
#           Service = "events.amazonaws.com"
#         }
#       }
#     ]
#   })

#   inline_policy {
#     name = "invoke-step-function"
#     policy = jsonencode({
#       Version = "2012-10-17"
#       Statement = [
#         {
#           Action   = "states:StartExecution"
#           Effect   = "Allow"
#           Resource = aws_sfn_state_machine.inference_sfn.arn
#         }
#       ]
#     })
#   }
# }
