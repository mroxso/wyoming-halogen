# Container publishing

The container workflow builds Linux AMD64 and ARM64 images on branch pushes,
all tag pushes, pull requests, and manual runs.

GHCR login and image publication are allowed only when the run is not a pull
request and its ref is `refs/heads/main` or starts with `refs/tags/`.
This also restricts manual runs: selecting another branch builds without publishing.

Main publishes branch, SHA, and latest image tags. Git tag builds publish SHA
tags; semantic version tags also produce semantic version image tags.
Other branches and pull requests validate builds without pushing images.
