# Script para configurar o PATH do Python 3.12
$pythonPaths = @(
    "C:\Python312",
    "C:\Python312\Scripts",
    "C:\Users\$env:USERNAME\AppData\Local\Programs\Python\Python312",
    "C:\Users\$env:USERNAME\AppData\Local\Programs\Python\Python312\Scripts",
    "C:\Program Files\Python312",
    "C:\Program Files\Python312\Scripts"
)

function Add-ToPathIfExists {
    param ([string]$path)
    if (Test-Path $path) {
        $currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
        if (-not $currentPath.Contains($path)) {
            [Environment]::SetEnvironmentVariable("Path", "$currentPath;$path", "User")
            Write-Host "Adicionado ao PATH: $path"
        }
    }
}

foreach ($path in $pythonPaths) {
    Add-ToPathIfExists $path
}

Write-Host "Configuracao do PATH concluida. Por favor, reinicie o PowerShell."
