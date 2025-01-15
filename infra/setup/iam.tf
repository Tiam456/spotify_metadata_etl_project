# create iam for continuous delivery user (api user)

resource "aws_iam_user" "cd_user" {
  name = "cd_user"
}

resource "aws_iam_access_key" "cd_user" {
  user = aws_iam_user.cd_user.name
}

# terraform backend
data "aws_iam_policy_document" "tf_backend" {
  statement {
    effect    = "Allow"
    actions   = ["s3:ListBucket"]
    resources = ["arn:aws:s3:::${var.state_bucket_name}"]
  }
  statement {
    effect  = "Allow"
    actions = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"]
    resources = [
      "arn:aws:s3:::${var.state_bucket_name}/tf-state-deploy/*",
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
    resources = ["arn:aws:dynamodb:*:*:table/${var.dynamodb_table_name}"]
  }
}

resource "aws_iam_policy" "tf_backend" {
  name        = "${aws_iam_user.cd_user.name}-tf-s3-dynamodb"
  description = "Allow S3 and DynamoDB resources for TF backend resources"
  policy      = data.aws_iam_policy_document.tf_backend.json
  # in theory, the data section can be translated to json and to be used here
}

resource "aws_iam_user_policy_attachment" "tf_backend" {
  user       = aws_iam_user.cd_user.name
  policy_arn = aws_iam_policy.tf_backend.arn
}
