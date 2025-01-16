# create ecr repositories

resource "aws_ecr_repository" "app" {
  name                 = "spotify-metadata-etl-project"
  image_tag_mutability = "MUTABLE"
  force_delete         = true
  image_scanning_configuration {
    scan_on_push = true # make sure updated security patches are applied
  }
}
