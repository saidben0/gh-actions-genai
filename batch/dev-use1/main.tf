module "dev-use1" {
  source                   = "../module"
  python_version           = var.python_version
  lambda_role_name         = var.lambda_role_name
  lambda_layer_version_arn = var.lambda_layer_version_arn

  inputs_bucket_name = var.inputs_bucket_name
  # lambda_function_name     = var.lambda_function_name
  # dynamodb_table_name      = var.dynamodb_table_name
  # system_prompt_ver        = var.system_prompt_ver
  # security_grp_id          = var.security_grp_id
  # subnet_id                = var.subnet_id

  env  = var.env
  tags = var.tags

  providers = {
    aws.acc   = aws.use1
    awscc.acc = awscc.use1
  }
}
