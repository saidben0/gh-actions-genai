resource "awscc_bedrock_prompt" "this" {
  for_each = local.bedrock_prompts

  provider        = awscc.acc
  default_variant = each.value.default_variant
  name            = each.value.name
  variants        = each.value.variants

  tags = var.tags
}


resource "null_resource" "main_prompt_version_ssm_param" {
  provisioner "local-exec" {
    command = <<EOT
      VERSION_NUM=$(aws bedrock-agent create-prompt-version --prompt-identifier ${local.prompt_id} | grep -i version | awk -F'"' '{print $4}')
      aws ssm put-parameter \
          --name "/${var.prefix}/${var.env}/bedrock/prompts/${local.prompt_id}/versions/$VERSION_NUM" \
          --type "String" \
          --value "$VERSION_NUM" \
          --overwrite || true
    EOT
  }

  triggers = {
    filebasesha = "${base64sha256(file("${path.module}/templates/prompt_template.txt"))}"
  }
  depends_on = [awscc_bedrock_prompt.this]
}

resource "null_resource" "system_prompt_version_ssm_param" {
  provisioner "local-exec" {
    command = <<EOT
      VERSION_NUM=$(aws bedrock-agent create-prompt-version --prompt-identifier ${local.system_prompt_id} | grep -i version | awk -F'"' '{print $4}')
      aws ssm put-parameter \
          --name "/${var.prefix}/${var.env}/bedrock/prompts/${local.system_prompt_id}/versions/$VERSION_NUM" \
          --type "String" \
          --value "$VERSION_NUM" \
          --overwrite || true
    EOT
  }

  triggers = {
    filebasesha = "${base64sha256(file("${path.module}/templates/system_prompt_template.txt"))}"
  }
  depends_on = [awscc_bedrock_prompt.this]
}

resource "null_resource" "tesseract_main_prompt_version_ssm_param" {
  provisioner "local-exec" {
    command = <<EOT
      VERSION_NUM=$(aws bedrock-agent create-prompt-version --prompt-identifier ${local.tesseract_prompt_id} | grep -i version | awk -F'"' '{print $4}')
      aws ssm put-parameter \
          --name "/${var.prefix}/${var.env}/bedrock/prompts/${local.tesseract_prompt_id}/versions/$VERSION_NUM" \
          --type "String" \
          --value "$VERSION_NUM" \
          --overwrite || true
    EOT
  }

  triggers = {
    filebasesha = "${base64sha256(file("${path.module}/templates/tesseract_prompt_template.txt"))}"
  }
  depends_on = [awscc_bedrock_prompt.this]
}

resource "null_resource" "tesseract_system_prompt_version_ssm_param" {
  provisioner "local-exec" {
    command = <<EOT
      VERSION_NUM=$(aws bedrock-agent create-prompt-version --prompt-identifier ${local.tesseract_system_prompt_id} | grep -i version | awk -F'"' '{print $4}')
      aws ssm put-parameter \
          --name "/${var.prefix}/${var.env}/bedrock/prompts/${local.tesseract_system_prompt_id}/versions/$VERSION_NUM" \
          --type "String" \
          --value "$VERSION_NUM" \
          --overwrite || true
    EOT
  }

  triggers = {
    filebasesha = "${base64sha256(file("${path.module}/templates/tesseract_system_prompt_template.txt"))}"
  }
  depends_on = [awscc_bedrock_prompt.this]
}

resource "awscc_bedrock_prompt_version" "this" {
  for_each = local.bedrock_prompts

  provider   = awscc.acc
  prompt_arn = awscc_bedrock_prompt.this[each.key].arn

  # tags = var.tags
}

data "awscc_bedrock_prompt_version" "main_prompt" {
  provider = awscc.acc
  id       = awscc_bedrock_prompt_version.this["mainPrompt"].id

  depends_on = [null_resource.main_prompt_version_ssm_param]
}

data "awscc_bedrock_prompt_version" "system_prompt" {
  provider = awscc.acc
  id       = awscc_bedrock_prompt_version.this["systemPrompt"].id

  depends_on = [null_resource.system_prompt_version_ssm_param]
}
