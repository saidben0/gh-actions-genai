variable "prefix" {
  type    = string
  default = "llandman-batch"
}

variable "env" {
  type = string
}

variable "lambda_role_name" {
  type = string
}

variable "lambda_layer_version_arn" {
  type = string
}

variable "python_version" {
  type = string
}

variable "tags" {
  type = map(string)
  default = {
    Team         = "Tech-Land-Manufacturing@enverus.com"
    Dataset      = "land"
    SourceCode   = "https://github.com/enverus-ea/land.llandman"
    Component    = "llandman"
    BusinessUnit = "ea"
    Product      = "courthouse"
    Environment  = "dev"
  }
}



variable "inputs_bucket_name" {
  type    = string
  default = "enverus-courthouse-dev-chd-plants-20241023"
}

# variable "lambda_function_name" {
#   type    = string
#   default = "queue-processing"
# }

# variable "lambda_role_name" {
#   type    = string
#   default = "llandman-dev-lambda-exec-role"
# }

# variable "dynamodb_table_name" {
#   type    = string
#   default = "model-outputs"
# }

# variable "prompt_ver" {
#   type    = string
#   default = "1"
# }

# variable "system_prompt_id" {
#   type    = string
#   default = "IB5O7AZE0G"
# }

# variable "system_prompt_ver" {
#   type    = string
#   default = "1"
# }

# variable "security_grp_id" {
#   type    = string
#   default = "sg-04e975365d5ef5219"
# }

# variable "subnet_id" {
#   type    = string
#   default = "subnet-01ac397cf39dce5ba"
# }
