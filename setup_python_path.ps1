# Script para configurar o PATH do Python
$pythonPaths = @(
    "C:\Python311",
    "C:\Python311\Scripts",
    "C:\Users\usuario\AppData\Local\Programs\Python\Python311",
    "C:\Users\usuario\AppData\Local\Programs\Python\Python311\Scripts",
    "C:\Program Files\Python311",
    "C:\Program Files\Python311\Scripts"
)

# Função para adicionar ao PATH se o diretório existir
function Add-ToPathIfExists {
    param (
        [string]$path
    )
    if (Test-Path $path) {
        $currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
        if (-not $currentPath.Contains($path)) {
            [Environment]::SetEnvironmentVariable("Path", "$currentPath;$path", "User")
            Write-Host "Adicionado ao PATH: $path"
        }
    }
}

# Adicionar cada caminho ao PATH se existir
foreach ($path in $pythonPaths) {
    Add-ToPathIfExists $path
}

Write-Host "Configuração do PATH concluída. Por favor, reinicie o PowerShell." 