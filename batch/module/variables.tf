variable "prefix" {
  type    = string
  default = "llandman"
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

variable "python_version" {
  type = string
}



variable "inputs_bucket_name" {
  type    = string
  default = "enverus-courthouse-dev-chd-plants-20241023"
}

# variable "lambda_function_name" {
#   type    = string
#   default = "queue-processing"
# }

# variable "dynamodb_table_name" {
#   type    = string
#   default = "model-outputs"
# }

# variable "kms_alias_name" {
#   type    = string
#   default = "key-alias"
# }

# variable "project_name" {
#   type    = string
#   default = "land-doc-processing"
# }

# variable "prompt_ver" {
#   type    = string
#   default = "1"
# }

# variable "system_prompt_ver" {
#   type    = string
#   default = "1"
# }

# variable "security_grp_id" {
#   type = string
# }

# variable "subnet_id" {
#   type = string
# }
