# tools/check-covers.ps1 - CI check for RED FIELD cover assets (feed/image_gen.py).
# Fails (exit 1) if:
#   * manifest.json is absent;
#   * any PNG is missing;
#   * any ASSET_HASH does not match CONTENT_ID + DESIGN_VERSION;
#   * any DESIGN_VERSION changed without reissue.
# Exit 0 when the whole cover set is current.
param()
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Push-Location $root
try {
    if (-not (Test-Path 'feed\images\manifest.json')) {
        Write-Output 'FAIL manifest.json missing'
        exit 1
    }
    python -m unittest feed.tests.test_image_gen_versioning -q
    if ($LASTEXITCODE -ne 0) {
        Write-Output 'FAIL unit tests'
        exit $LASTEXITCODE
    }
    python feed\image_gen.py --verify
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}