$baseUrl = "https://help.tdx.com.cn"
$mainPage = "/quant/"
$outputDir = "tdx_quant_site"

# 创建输出目录
if (!(Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir | Out-Null
}

Write-Host "============================================"
Write-Host "通达信量化文档爬虫 - PowerShell版"
Write-Host "============================================"

# 步骤1: 获取主页，提取侧边栏所有链接
Write-Host "`n[1/2] 获取主页链接..."
$response = Invoke-WebRequest -Uri "$baseUrl$mainPage" -UseBasicParsing -TimeoutSec 30
$html = $response.Content

# 提取侧边栏链接
$links = [regex]::Matches($html, 'href="(/quant/[^"]+\.html[^"]*)"') | ForEach-Object { $_.Groups[1].Value }
$links = $links | Select-Object -Unique | Sort-Object

# 也提取没有.html的链接（章节页）
$chapterLinks = [regex]::Matches($html, 'href="(/quant/docs/markdown/[^"]+?)"(?=\s+class)') | ForEach-Object { $_.Groups[1].Value }
$chapterLinks = $chapterLinks | Where-Object { $_ -notmatch '\.html$' } | Select-Object -Unique

$allLinks = @($links) + @($chapterLinks) | Select-Object -Unique | Sort-Object

Write-Host "找到 $($allLinks.Count) 个页面`n"

# 步骤2: 逐个下载
$success = 0
$fail = 0
$retryCount = 3
$baseDelay = 2

foreach ($i in 0..($allLinks.Count - 1)) {
    $link = $allLinks[$i]
    $url = "$baseUrl$link"
    Write-Host "[$($i+1)/$($allLinks.Count)] $link" -NoNewline
    
    $downloaded = $false
    for ($attempt = 1; $attempt -le $retryCount; $attempt++) {
        try {
            $resp = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 30
            $content = $resp.Content
            
            # 确定保存路径
            $path = $link -replace '/quant/', ''
            $path = $path.TrimEnd('/')
            if ([string]::IsNullOrEmpty($path)) { $path = "index.html" }
            elseif ($path -notmatch '\.html$') { $path = "$path.html" }
            
            $filePath = Join-Path $outputDir $path
            $dir = Split-Path $filePath -Parent
            if (!(Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
            
            [System.IO.File]::WriteAllText($filePath, $content, [System.Text.Encoding]::UTF8)
            Write-Host " ✓ ($($content.Length) bytes)"
            $downloaded = $true
            $success++
            break
        }
        catch {
            $delay = $baseDelay * [Math]::Pow(2, $attempt - 1)
            $random = Get-Random -Minimum 500 -Maximum 1500
            $delay = $delay + ($random / 1000)
            Write-Host " ⚠ 重试 $attempt/$retryCount (等待 ${delay}s)..." -ForegroundColor Yellow
            Start-Sleep -Seconds $delay
        }
    }
    
    if (!$downloaded) {
        Write-Host " ✖ 失败" -ForegroundColor Red
        $fail++
    }
    
    # 请求间隔（平滑递减）
    if ($i -lt ($allLinks.Count - 1)) {
        $delay = [Math]::Max(1, 3 - ($success * 0.1))
        $jitter = Get-Random -Minimum 0 -Maximum 1000
        $delay = $delay + ($jitter / 1000)
        Start-Sleep -Milliseconds ([int]($delay * 1000))
    }
}

Write-Host "`n============================================"
Write-Host "完成! 成功: $success  失败: $fail"
Write-Host "保存目录: $outputDir/"
Write-Host "============================================"
