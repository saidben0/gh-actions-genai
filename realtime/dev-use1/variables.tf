variable "prefix" {
  type    = string
  default = "llandman"
}

variable "env" {
  type    = string
  default = "dev"
}

variable "inputs_bucket_name" {
  type    = string
  default = "enverus-courthouse-dev-chd-plants"
  # default = "enverus-courthouse-dev-chd-plants-0823" # for testing in proserve shared acc
}

variable "lambda_function_name" {
  type    = string
  default = "queue-processing"
}

variable "lambda_role_name" {
  type    = string
  default = "llandman-dev-lambda-exec-role"
}

variable "dynamodb_table_name" {
  type    = string
  default = "model-outputs"
}

variable "python_version" {
  type = string
}

variable "tags" {
  type = map(string)
  default = {
    GitRepo     = "Land.Llandman"
    Environment = "Dev"
    Owner       = "Ops"
  }
}


variable "prompt_ver" {
  type    = string
  default = "1"
}

# variable "system_prompt_id" {
#   type    = string
#   default = "IB5O7AZE0G"
# }

variable "system_prompt_ver" {
  type    = string
  default = "1"
}

variable "lambda_layer_version_arn" {
  type = string
}
