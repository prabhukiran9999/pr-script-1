# provider "aws" {
#   region = "ca-central-1"
#   alias  = "master-account"
# }

terraform {
  required_providers {
    aws = {
      source = "hashicorp/aws"
      version = "4.40.0"
    }
  }
    backend "s3" {
    bucket = "test-tfstate-migaration-bucket"
    key    = "path/to/my/state"
    dynamodb_table = "tf-state-lockfiles"
    region = "ca-central-1"
  }

}
# provider "aws" {
#   region = "ca-central-1"
#   alias  = "operations-account"

#   assume_role {
#     role_arn     = "arn:aws:iam::${local.operations_account.id}:role/AWSCloudFormationStackSetExecutionRole"
#     session_name = "terraform-sea-automation"
#   }
# }

# module "lz_info" {
#   source = "github.com/BCDevOps/terraform-aws-sea-organization-info"
#   providers = {
#     aws = aws.master-account
#   }
# }

# locals {
#   operations_account = [for account in module.lz_info.core_accounts : account if account.name == "Operations"][0]
# }


// resources in the Operations account

# data "aws_security_group" "sg" {
#   provider = aws.operations-account
#   name     = var.sg_name
# }

# data "aws_subnet" "subnet" {
#   provider = aws.operations-account
#   filter {
#     name   = "tag:Name"
#     values = [var.subnet_name]
#   }
# }


# resource "aws_iam_role" "github-runner-role" {
#   provider = aws.operations-account

#   name = "Github_OIDC_Runner_Role"

#   assume_role_policy = <<EOF
# {
#     "Version": "2012-10-17",
#     "Statement": [
#         {
#             "Effect": "Allow",
#             "Principal": {
#                 "Federated": "arn:aws:iam::${local.operations_account.id}:oidc-provider/token.actions.githubusercontent.com"
#             },
#             "Action": "sts:AssumeRoleWithWebIdentity",
#             "Condition": {
#                 "ForAllValues:StringLike": {
#                     "token.actions.githubusercontent.com:sub": "repo:bcgov-c/aws-ecf-*-:*",
#                     "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
#                 }
#             }
#         }
#     ]
# }
# EOF
# }

# resource "aws_iam_role_policy" "github-runner-role" {
#   provider = aws.operations-account

#   name = "Github_OIDC_Runner_Policy"
#   role = aws_iam_role.github-runner-role.id

#   policy = <<-EOF
# {
#     "Version": "2012-10-17",
#     "Statement": [
#         {
#             "Sid": "Runner",
#             "Effect": "Allow",
#             "Action": [
#                 "ec2:DescribeInstances",
#                 "ec2:TerminateInstances",
#                 "ec2:StartInstances",
#                 "ec2:CreateTags",
#                 "ec2:RunInstances",
#                 "ec2:StopInstances",
#                 "ec2:AssociateIamInstanceProfile",
#                 "ec2:ReplaceIamInstanceProfileAssociation",
#                 "ec2:DescribeInstanceStatus"
#             ],
#             "Resource": "*"
#         }
#     ]
# }
# EOF
# }


# data "aws_ami" "amazon_linux" {
#   provider    = aws.operations-account
#   most_recent = true


#   filter {
#     name   = "name"
#     values = ["amzn2-ami-kernel-5.10-hvm-*"]
#   }

#   filter {
#     name   = "virtualization-type"
#     values = ["hvm"]
#   }

#   filter {
#     name   = "root-device-type"
#     values = ["ebs"]
#   }

#   filter {
#     name   = "architecture"
#     values = ["x86_64"]
#   }
# }

# resource "aws_instance" "runner" {
#   provider               = aws.operations-account
#   ami                    = data.aws_ami.amazon_linux.id
#   instance_type          = var.instance_type
#   subnet_id              = data.aws_subnet.subnet.id
#   iam_instance_profile   = aws_iam_instance_profile.test_profile.name
#   vpc_security_group_ids = [data.aws_security_group.sg.id]
#   user_data              = <<EOF
#   #!/bin/bash
#   sudo yum update -y
#   sudo yum install git -y
#   sudo yum install docker -y
#   sudo service docker start

# EOF
#   root_block_device {
#     volume_size = "100"
#     volume_type = "gp2"
#     encrypted   = true
#   }
#   tags = {
#     Name = "GitHub_runner"
#   }
# }

resource "aws_s3_bucket" "state_bucket" {
  bucket   = "workloads-state-bucket-operations-172621"
}

resource "aws_s3_bucket_acl" "state_bucket_acl" {
  bucket   = aws_s3_bucket.state_bucket.id
  acl      = "private"
}

resource "aws_s3_bucket_versioning" "bucket_versioning" {
  bucket   = aws_s3_bucket.state_bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_dynamodb_table" "dynamodb-terraform-state-lock" {
  name           = "terraform-state-lock-dynamo"
  hash_key       = "LockID"
  read_capacity  = 20
  write_capacity = 20

  attribute {
    name = "LockID"
    type = "S"
  }
}

# resource "aws_iam_instance_profile" "test_profile" {
#   provider       = aws.operations-account
#   name = "test_profile-${local.operations_account.id}"
#   role = aws_iam_role.role.name
# }

# resource "aws_iam_role" "role" {
#   provider       = aws.operations-account
#   name = "test_role-${local.operations_account.id}"
#   path = "/"

#   assume_role_policy = <<EOF
# {
#     "Version": "2012-10-17",
#     "Statement": [
#         {
#             "Action": "sts:AssumeRole",
#             "Principal": {
#                "Service": "ec2.amazonaws.com"
#             },
#             "Effect": "Allow",
#             "Sid": ""
#         }
#     ]
# }
# EOF
# }


