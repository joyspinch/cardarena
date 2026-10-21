# 卡牌竞技 构建：编译 client/src/ 下全部 .zan → 可执行文件。
#
# 公共包（Gui / Game.Kit / Game.Foundation / Game.Tactics …）住在 zan-lang
# 仓库的 packages/ 下，编译要带 --package-project 指向**包根所在的仓库根**：
# 仓库内 = 仓库根；项目搬到仓库外后 = zan-lang 仓库，由 $env:ZAN_HOME 或
# -PackageProject 指定。
# assets/ 由 zanc 自动内嵌进 exe（入口源文件带目录前缀时才会定位到），
# 这里再在 exe 旁留一份磁盘副本——运行时磁盘优先，换图即生效。
param(
    [string]$Compiler = $env:ZANC,
    [string]$Stdlib = $env:ZAN_STDLIB,
    [string]$Output = '',
    [string]$PackageProject = '',
    # 发布成单文件 exe（自带运行库与资源）
    [switch]$Publish,
    # 透传给 zanc 的额外参数（如 --target android-arm64 ...）
    [string[]]$ZancArgs = @()
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
            # 兜底：工作区里固定位置的编译器（可用 -Compiler 覆盖）。
            $fallback = 'D:/project/zan-lang/build/zanc.exe'
            if (-not (Test-Path $fallback)) {
                throw '找不到 zanc：请设 $env:ZAN_HOME、$env:ZANC，或用 -Compiler 指定编译器路径'
            }
            $Compiler = $fallback
        }
    }
}
if (-not $Stdlib -and $env:ZAN_HOME) { $Stdlib = Join-Path $env:ZAN_HOME 'stdlib' }
if (-not $PackageProject) {
    if ($env:ZAN_HOME) {
        $PackageProject = $env:ZAN_HOME
    } else {
        throw '需要 -PackageProject 指向含 packages/ 的仓库根（如 D:/project/zan-lang）'
    }
}
if (-not $Output) { $Output = Join-Path $repo 'build/cardarena' }
$Output = [IO.Path]::GetFullPath($Output)
New-Item -ItemType Directory -Force -Path $Output | Out-Null
# 入口 main.zan 必须排第一：zanc 只把 Main() 给第一个编译输入
# （genrun.c 的 emitMain=paths[0]）。其余 .zan 递归枚举——zanc 不会自动
# 带上同目录的其它文件，少传一个就是 "undefined type"。
$entry = Join-Path $project 'src/main.zan'
$sources = @()
if (Test-Path $entry) { $sources += $entry }
$sources += @(Get-ChildItem (Join-Path $project 'src') -Recurse -File -Filter *.zan |
    Where-Object { $_.FullName -ne $entry } | Sort-Object FullName | ForEach-Object { $_.FullName })
$zargs = @($sources) + @('--auto-stdlib', '--package-project', $PackageProject)
if ($Stdlib) { $zargs += @('--stdlib-path', $Stdlib) }
if ($Publish) { $zargs += @('--publish') }
if ($ZancArgs) { $zargs += $ZancArgs }
$exe = Join-Path $Output 'Cardarena.exe'
$zargs += @('-o', $exe)
& $Compiler @zargs
if ($LASTEXITCODE -ne 0) { throw "zanc failed ($LASTEXITCODE)" }
# 素材拷到 exe 旁（拷**内容**，不是目录本身——否则重跑会套出 assets/assets）。
# 下划线开头的是一次性自检文件，不进 exe。
$assets = Join-Path $project 'assets'
if (Test-Path $assets) {
    $dest = Join-Path $Output 'assets'
    New-Item -ItemType Directory -Force -Path $dest | Out-Null
    Get-ChildItem $assets -Recurse -File | Where-Object { -not $_.Name.StartsWith('_') } |
        ForEach-Object {
            $target = Join-Path $dest $_.FullName.Substring($assets.Length + 1)
            New-Item -ItemType Directory -Force -Path (Split-Path -Parent $target) | Out-Null
            Copy-Item $_.FullName $target -Force
        }
}
# 皮肤包另拷一份到 **exe 同级**的 skins/<名字>/：Gui.Styling.Skin.Roots
# 会找 exe 同级的 skins/ 与 assets/skins/，两处都放最稳（放 assets/ 下
# 只有在 exe 同级也有 assets/skins/ 时才找得到）。
$skins = Join-Path $assets 'skins'
if (Test-Path $skins) {
    $skinDest = Join-Path $Output 'skins'
    New-Item -ItemType Directory -Force -Path $skinDest | Out-Null
    Get-ChildItem $skins -Directory | ForEach-Object {
        $target = Join-Path $skinDest $_.Name
        New-Item -ItemType Directory -Force -Path $target | Out-Null
        Copy-Item (Join-Path $_.FullName '*') $target -Recurse -Force
    }
}

# 控件基线 base.css **不在这里拷**：zanc 会自动内嵌 stdlib 的 Gui 皮肤基线
# （含 base.css 与 dark/light——见 src/compiler/main.c 的 skins 自动内嵌分支；
# embedres 的过滤器只作用于 depth-1 的皮肤包目录，base.css 是文件照内嵌）。
# 运行时 Gui 也是磁盘优先、内嵌兜底（Gui.Styling.Skin.BaseCss），所以 exe 旁
# 不必再放一份 base.css——省掉它还免了"磁盘旧基线盖住 exe 内嵌新基线"的漂移。
# 只有"整体替换基线"（自带完整 base.css 替身）才会让编译器跳过基线自动内嵌。
# 清掉旧版遗留的磁盘 base.css（老构建拷过一份）：留着会盖住 exe 内嵌的
# 基线，让"内嵌兜底到底有没有生效"这件事永远测不出来。
$staleBase = Join-Path $Output 'skins/base.css'
if (Test-Path $staleBase) { Remove-Item $staleBase -Force }
Write-Host "Built $exe"
