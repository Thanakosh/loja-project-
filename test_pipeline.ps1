# Script de teste do pipeline de Importar Nota
# Executa: .\test_pipeline.ps1

$BASE = "http://localhost:8000/api/v1"
$XML_PATH = "$env:USERPROFILE\Downloads\NFe52250974200403000625550010009933661197691742.xml"
$PDF_PATH = "$env:USERPROFILE\Downloads\Fralda Pampers Pants Ajuste Total Max Xxxg 54 Unidades.pdf"
$IMG_PATH = "$env:USERPROFILE\Downloads\image.jpg"

Write-Host "`n===== TESTE DO PIPELINE IMPORTAR NOTA =====" -ForegroundColor Cyan

# 1. Login
Write-Host "`n[1/5] Fazendo login..." -ForegroundColor Yellow
$loginBody = @{ username = "admin"; password = "admin" }
try {
    $login = Invoke-RestMethod -Uri "$BASE/auth/login" -Method Post -Body $loginBody -ContentType "application/x-www-form-urlencoded"
    $TOKEN = $login.access_token
    Write-Host "     OK - Token obtido" -ForegroundColor Green
} catch {
    Write-Host "     FALHOU: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "     Tentando com usuario padrao..." -ForegroundColor Yellow
    # Tentar descobrir usuario
    try {
        $login = Invoke-RestMethod -Uri "$BASE/auth/login" -Method Post -Body @{ username = "usuario"; password = "senha123" } -ContentType "application/x-www-form-urlencoded"
        $TOKEN = $login.access_token
        Write-Host "     OK - Token obtido" -ForegroundColor Green
    } catch {
        Write-Host "     FALHOU - Nao foi possivel obter token. Verifique credenciais." -ForegroundColor Red
        exit 1
    }
}

$headers = @{ Authorization = "Bearer $TOKEN" }

# 2. Testar upload XML
Write-Host "`n[2/5] Testando upload XML (NFe real)..." -ForegroundColor Yellow
if (Test-Path $XML_PATH) {
    try {
        $form = @{ file = Get-Item $XML_PATH }
        $result = Invoke-RestMethod -Uri "$BASE/ocr/upload-arquivo" -Method Post -Headers $headers -Form $form
        Write-Host "     OK - Status: $($result.status) | Task: $($result.task_id)" -ForegroundColor Green
        Write-Host "     Mensagem: $($result.message)" -ForegroundColor Gray
        $XML_TASK = $result.task_id

        # Buscar resultado do XML (deve ser imediato)
        Start-Sleep -Milliseconds 500
        $status = Invoke-RestMethod -Uri "$BASE/ocr/status/$XML_TASK" -Method Get -Headers $headers
        Write-Host "     Status final: $($status.status)" -ForegroundColor Green
        if ($status.result.nota_fiscal) {
            $nf = $status.result.nota_fiscal
            Write-Host "     Fornecedor: $($nf.fornecedor)" -ForegroundColor Cyan
            Write-Host "     NF numero: $($nf.numero_nota)" -ForegroundColor Cyan
            Write-Host "     Produtos encontrados: $($nf.produtos.Count)" -ForegroundColor Cyan
            Write-Host "     Valor total: R$ $($nf.valor_total)" -ForegroundColor Cyan
            Write-Host "     Fornecedor status: $($nf.fornecedor_status)" -ForegroundColor Cyan
        }
    } catch {
        Write-Host "     FALHOU: $($_.Exception.Message)" -ForegroundColor Red
    }
} else {
    Write-Host "     PULADO - arquivo nao encontrado: $XML_PATH" -ForegroundColor DarkYellow
}

# 3. Testar idempotencia (mesmo XML de novo)
Write-Host "`n[3/5] Testando idempotencia (mesmo XML novamente)..." -ForegroundColor Yellow
if (Test-Path $XML_PATH) {
    try {
        $form = @{ file = Get-Item $XML_PATH }
        $result2 = Invoke-RestMethod -Uri "$BASE/ocr/upload-arquivo" -Method Post -Headers $headers -Form $form
        if ($result2.task_id -eq $XML_TASK) {
            Write-Host "     OK - Reutilizou task existente (cache funcionando)" -ForegroundColor Green
        } else {
            Write-Host "     AVISO - Criou nova task ao inves de reutilizar: $($result2.task_id)" -ForegroundColor DarkYellow
        }
    } catch {
        Write-Host "     FALHOU: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# 4. Testar upload PDF
Write-Host "`n[4/5] Testando upload PDF..." -ForegroundColor Yellow
if (Test-Path $PDF_PATH) {
    try {
        $form = @{ file = Get-Item $PDF_PATH }
        $result = Invoke-RestMethod -Uri "$BASE/ocr/upload-arquivo" -Method Post -Headers $headers -Form $form
        Write-Host "     OK - Status: $($result.status) | Task: $($result.task_id)" -ForegroundColor Green
        Write-Host "     (PDF requer Gemini API Key para processar)" -ForegroundColor Gray
    } catch {
        Write-Host "     FALHOU: $($_.Exception.Message)" -ForegroundColor Red
    }
} else {
    Write-Host "     PULADO - arquivo nao encontrado: $PDF_PATH" -ForegroundColor DarkYellow
}

# 5. Testar upload Imagem
Write-Host "`n[5/5] Testando upload Imagem..." -ForegroundColor Yellow
if (Test-Path $IMG_PATH) {
    try {
        $form = @{ file = Get-Item $IMG_PATH }
        $result = Invoke-RestMethod -Uri "$BASE/ocr/upload-arquivo" -Method Post -Headers $headers -Form $form
        Write-Host "     OK - Status: $($result.status) | Task: $($result.task_id)" -ForegroundColor Green
        Write-Host "     (Imagem requer Gemini API Key para processar)" -ForegroundColor Gray
    } catch {
        Write-Host "     FALHOU: $($_.Exception.Message)" -ForegroundColor Red
    }
} else {
    Write-Host "     PULADO - arquivo nao encontrado: $IMG_PATH" -ForegroundColor DarkYellow
}

Write-Host "`n===== TESTE CONCLUIDO =====" -ForegroundColor Cyan
