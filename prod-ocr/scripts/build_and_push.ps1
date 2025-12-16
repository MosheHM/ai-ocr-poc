param (
    [Parameter(Mandatory=$true)]
    [string]$Version
)

$ImageName = "prod-ocr"
$DockerUsername = "moshehmakias"
$FullImageName = "$DockerUsername/$ImageName`:$Version"

Write-Host "Building Docker image: $FullImageName..."
docker build -t "$ImageName`:$Version" .

if ($LASTEXITCODE -eq 0) {
    Write-Host "Tagging image..."
    docker tag "$ImageName`:$Version" $FullImageName

    if ($LASTEXITCODE -eq 0) {
        Write-Host "Pushing image to Docker Hub..."
        docker push $FullImageName
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Done! Image pushed to $FullImageName"
        } else {
            Write-Error "Failed to push image."
        }
    } else {
        Write-Error "Failed to tag image."
    }
} else {
    Write-Error "Failed to build image."
}
