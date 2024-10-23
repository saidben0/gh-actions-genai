terraform {
  backend "s3" {
    bucket = "di-dev-terraform-155185327318"
    key    = "dev/llandman/terraform.batch.tfstate"
    region = "us-east-1"
  }
}
