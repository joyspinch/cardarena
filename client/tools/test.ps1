# 卡牌竞技 三段测试：
#   1) 玩法断言（client/tests/cardarena_test.zan，无头）
#   2) 存档两遍（第一遍写盘、第二遍是新进程读回：场次 1 -> 2）
#   3) 无头冒烟（程序跑满对局并自行退出）
param(
    [string]$Compiler = $env:ZANC,
    [string]$PackageProject = '',
    [int]$TimeoutSeconds = 180
)
$ErrorActionPreference = 'Stop'
$project = Split-Path -Parent $PSScriptRoot
$repo = Split-Path -Parent $project
if (-not $Compiler) {
    $local = if ($env:ZAN_HOME) { Join-Path $env:ZAN_HOME 'build/zanc.exe' } else { '' }
    if ($local -and (Test-Path $local)) {
        $Compiler = $local
    } else {
        $cmd = Get-Command zanc -ErrorAction SilentlyContinue
        if ($cmd) {
            $Compiler = $cmd.Source
        } else {
            $fallback = 'D:/project/zan-lang/build/zanc.exe'
            if (-not (Test-Path $fallback)) {
                throw '找不到 zanc：请设 $env:ZAN_HOME、$env:ZANC，或用 -Compiler 指定编译器路径'
            }
            $Compiler = $fallback
        }
    }
}
if (-not $PackageProject) {
    if ($env:ZAN_HOME) {
        $PackageProject = $env:ZAN_HOME
    } else {
        throw '需要 -PackageProject 指向含 packages/ 的仓库根（如 D:/project/zan-head）'
    }
}
$out = Join-Path $repo 'build/cardarena'
& (Join-Path $PSScriptRoot 'build.ps1') -Compiler $Compiler -PackageProject $PackageProject -Output $out
$exe = Join-Path $out 'Cardarena.exe'
if (-not (Test-Path $exe)) { throw "缺少可执行文件：$exe" }

# --- 1) 玩法断言用例 ---
# 卡牌目录 / 牌库抽牌与重洗 / 牌组构筑 / 能量与出牌 / 攻击与防御 /
# 技能 / 回合推进 / AI 策略 / 胜负判定 / 3 个种子的完整对局。
# 源码要排除 main.zan（它带 Main()，用例自己的 Main 才是入口）。
$caseSources = @(Get-ChildItem (Join-Path $project 'src') -Recurse -File -Filter *.zan |
    Where-Object { $_.Name -ne 'main.zan' } |
    Sort-Object FullName | ForEach-Object { $_.FullName })
$case = 'cardarena_test.zan'
$stem = [IO.Path]::GetFileNameWithoutExtension($case)
$caseExe = Join-Path $out "$stem.exe"
& $Compiler (@((Join-Path $project "tests/$case")) + $caseSources +
    @('--auto-stdlib', '--package-project', $PackageProject, '-o', $caseExe))
if ($LASTEXITCODE -ne 0) { throw "玩法用例编译失败：$case (zanc=$LASTEXITCODE)" }
$caseOut = & $caseExe 2>&1 | Out-String
if ($LASTEXITCODE -ne 0) { throw "玩法用例失败：$case`n$caseOut" }
if ($caseOut -notmatch "$stem OK") { throw "玩法用例输出不对：$case`n$caseOut" }
Write-Host $caseOut.Trim()
Write-Host "${stem}_OK"

# 存档落在临时目录里，不碰玩家机器上的 %LOCALAPPDATA%/Cardarena。
$saveDir = Join-Path $out 'savetest'
if (Test-Path $saveDir) { Remove-Item $saveDir -Recurse -Force }
New-Item -ItemType Directory -Force $saveDir | Out-Null
$env:CARDARENA_SAVE = $saveDir
# 冒烟标记：双方自动对战，打完一整局自行退出。
$env:CARDARENA_SMOKE = '1'
$env:CARDARENA_FRAMES = '900'
$log = Join-Path $out 'cardarena_smoke.log'
if (Test-Path $log) { Remove-Item $log -Force }
$proc = Start-Process -FilePath $exe -WorkingDirectory $out -PassThru -WindowStyle Hidden `
    -RedirectStandardOutput $log -RedirectStandardError (Join-Path $out 'cardarena_smoke.err')
if (-not $proc.WaitForExit($TimeoutSeconds * 1000)) {
    $proc.Kill()
    throw "无头冒烟超时：应用没在 $TimeoutSeconds 秒内退出"
}
if ($proc.ExitCode -ne 0) { throw "无头冒烟失败：exit=$($proc.ExitCode)" }
if (-not (Select-String -Path $log -Pattern 'CARDARENA_SMOKE_OK' -Quiet)) {
    throw "无头冒烟未收尾（缺 CARDARENA_SMOKE_OK）：$log"
}
# 存档落盘 + 读回：第二遍是新进程，必须读回第一遍写的档（场次 1 -> 2）。
$saveLine = Select-String -Path $log -Pattern 'CARDARENA_SAVE' | Select-Object -First 1
if (-not $saveLine) { throw "没有存档输出行（CARDARENA_SAVE）：$log" }
if ($saveLine.Line -notmatch 'runs=1') {
    throw "第一遍存档没写成场次 1：$($saveLine.Line)"
}
if (-not (Test-Path (Join-Path $saveDir 'cardarena_slot0.json'))) {
    throw "存档文件没落盘：$saveDir"
}
$log2 = Join-Path $out 'cardarena_smoke2.log'
if (Test-Path $log2) { Remove-Item $log2 -Force }
$proc2 = Start-Process -FilePath $exe -WorkingDirectory $out -PassThru -WindowStyle Hidden `
    -RedirectStandardOutput $log2 -RedirectStandardError (Join-Path $out 'cardarena_smoke2.err')
if (-not $proc2.WaitForExit($TimeoutSeconds * 1000)) {
    $proc2.Kill()
    throw "第二遍无头冒烟超时"
}
if ($proc2.ExitCode -ne 0) { throw "第二遍无头冒烟失败：exit=$($proc2.ExitCode)" }
if (-not (Select-String -Path $log2 -Pattern 'CARDARENA_SMOKE_OK' -Quiet)) {
    throw "第二遍无头冒烟未收尾（缺 CARDARENA_SMOKE_OK）：$log2"
}
$saveLine2 = Select-String -Path $log2 -Pattern 'CARDARENA_SAVE' | Select-Object -First 1
if (-not $saveLine2 -or $saveLine2.Line -notmatch 'runs=2') {
    throw "第二遍没读回上一遍的存档（期望 runs=2）：$($saveLine2.Line)"
}
Write-Host "cardarena_SAVE_OK runs=1 -> runs=2"
Write-Host "cardarena_SMOKE_OK"
