# IAM User for CD
resource "aws_iam_user" "cd_user" {
  name = "${var.project}-cd-user"
}

resource "aws_iam_access_key" "cd_user" {
  user = aws_iam_user.cd_user.name
}

# Policy document for Terraform backend access
data "aws_iam_policy_document" "terraform_backend" {
  statement {
    effect    = "Allow"
    actions   = ["s3:ListBucket"]
    resources = [aws_s3_bucket.terraform_state.arn]
  }

  statement {
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject"
    ]
    resources = [
      "${aws_s3_bucket.terraform_state.arn}/tf-state/*"
    ]
  }

  statement {
    effect = "Allow"
    actions = [
      "dynamodb:DescribeTable",
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:DeleteItem"
    ]
    resources = [aws_dynamodb_table.terraform_locks.arn]
  }
}

# IAM policy using the document
resource "aws_iam_policy" "terraform_backend" {
  name        = "${var.project}-terraform-backend"
  description = "Policy for Terraform backend access to S3 and DynamoDB"
  policy      = data.aws_iam_policy_document.terraform_backend.json
}

# Attach policy to CD user
resource "aws_iam_user_policy_attachment" "cd_user_terraform_backend" {
  user       = aws_iam_user.cd_user.name
  policy_arn = aws_iam_policy.terraform_backend.arn
}
