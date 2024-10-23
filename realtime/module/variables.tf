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

variable "python_version" {
  type = string
}

variable "tags" {
  type    = map(string)
  default = {}
}

# variable "inputs_bucket_name" {
#   type    = string
#   default = "enverus-courthouse-dev-chd-plants"
# }



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

# variable "system_prompt_id" {
#   type    = string
#   default = "IB5O7AZE0G"
# }

# variable "system_prompt_ver" {
#   type    = string
#   default = "1"
# }

# variable "bedrock_prompts" {
#   type = map(object({
#     default_variant    = string
#     name               = string
#     variants           = list(object({
#       inference_configuration = object({
#         text = object({
#           temperature = number
#           top_p        = number
#           max_tokens   = number
#           top_k        = number
#         })
#       })
#       name                   = string
#       template_configuration = object({
#         text = object({
#           text = string
#         })
#       })
#       template_type = string
#     }))
#   }))
#   default = {
#     "mainPrompt" = {
#       default_variant = "variantOne"
#       name            = "mainPrompt"
#       variants = [
#         {
#           inference_configuration = {
#             text = {
#               temperature = 0
#               top_p        = 0.9900000095367432
#               max_tokens   = 300
#               top_k        = 250
#             }
#           }
#           name = "variantOne"
#           template_configuration = {
#             text = {
#               text = data.template_file.prompt_template.rendered
#             }
#           }
#           template_type = "TEXT"
#         }
#       ]
#     }
#     "systemPrompt" = {
#       default_variant = "variantTwo"
#       name            = "systemPrompt"
#       variants = [
#         {
#           inference_configuration = {
#             text = {
#               temperature = 0.5
#               top_p        = 0.9000000000000000
#               max_tokens   = 200
#               top_k        = 100
#             }
#           }
#           name = "variantTwo"
#           template_configuration = {
#             text = {
#               text = data.template_file.prompt_template.rendered
#             }
#           }
#           template_type = "TEXT"
#         }
#       ]
#     }
#   }
# }