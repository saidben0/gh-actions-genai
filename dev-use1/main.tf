module "dev-use1" {
  source               = "../module"
  inputs_bucket_name   = var.inputs_bucket_name
  lambda_function_name = var.lambda_function_name
  lambda_role_name     = var.lambda_role_name
  lambda_policy_name   = var.lambda_policy_name
  dynamodb_table_name  = var.dynamodb_table_name
  prompt_id            = var.prompt_id
  system_prompt_id     = var.system_prompt_id
  system_prompt_ver    = var.system_prompt_ver

  providers = {
    aws.acc = aws.use1
  }
}
