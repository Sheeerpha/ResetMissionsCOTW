# Gera o programa no seu PC e monta a pasta para enviar (sem passar pelo GitHub):
#   <projeto>\ResetMissionsCOTW_v<versão>\       (pasta com o .exe e os LEIA-ME)
#   <projeto>\ResetMissionsCOTW_v<versão>.zip    (a mesma pasta compactada)
# Uso: clique com o botão direito neste arquivo > "Executar com o PowerShell"
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$projeto = Split-Path $PSScriptRoot -Parent

# Versão lida do próprio programa (VERSAO = '0.9.5 (Beta)' -> v0.9.5-beta)
$linha = Select-String -Path cotw_app.py -Pattern "^VERSAO = '([0-9.]+)(.*)'" | Select-Object -First 1
$versao = 'v' + $linha.Matches[0].Groups[1].Value
if ($linha.Matches[0].Groups[2].Value -match 'Beta') { $versao += '-beta' }
$nome = "ResetMissionsCOTW_$versao"

if (-not (Test-Path .venv)) {
    py -3 -m venv .venv
    .venv\Scripts\python.exe -m pip install pyinstaller
}
.venv\Scripts\python.exe -X utf8 testes.py
if ($LASTEXITCODE -ne 0) { Write-Host 'Os testes falharam; o .exe NÃO foi gerado.'; exit 1 }

.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --onefile --windowed --name ResetMissionsCOTW cotw_app.py
if ($LASTEXITCODE -ne 0) { Write-Host 'Falha ao gerar o .exe.'; exit 1 }

$pasta = Join-Path $projeto $nome
$zip = Join-Path $projeto "$nome.zip"
if (Test-Path $pasta) { Remove-Item $pasta -Recurse -Force }
if (Test-Path $zip) { Remove-Item $zip -Force }
New-Item -ItemType Directory $pasta | Out-Null
Copy-Item 'dist\ResetMissionsCOTW.exe' $pasta
Copy-Item 'LEIA-ME (distribuicao).txt' (Join-Path $pasta 'LEIA-ME_PRIMEIRO.txt')
Copy-Item 'README (distribuicao).txt' (Join-Path $pasta 'README_FIRST.txt')
Copy-Item 'LEEME (distribuicao).txt' (Join-Path $pasta 'LEEME_PRIMERO.txt')
Compress-Archive -Path $pasta -DestinationPath $zip

Write-Host ''
Write-Host "Pronto! Para enviar: $zip"
