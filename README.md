# SpeakerToMic

把 Windows **系统扬声器正在播放的声音**，通过 VB-Cable 虚拟声卡转发为一个可选的**虚拟麦克风**。
无界面、后台常驻、异常自动重连；被动回环采集，不静音、不改道、不影响你正在听的物理扬声器。

> 在会议 / 直播 / 语音房软件里，把麦克风选择为 `CABLE Output (VB-Audio Virtual Cable)`，
> 对方即可听到你电脑播放的音乐、视频、游戏声（默认不混入你本人说话）。

## 特性

- 一键后台运行，无需任何配置，自动跟随系统默认输出。
- WASAPI 回环（loopback）只读采集，共享模式，不占用、不独占物理音频设备。
- 会话异常自动重连，长期驻留稳定。
- 提供免安装 exe，也支持从源码运行 / 自行打包。

## 工作原理

```
系统默认扬声器播放流
        │  (WASAPI loopback，只读旁听)
        ▼
  SpeakerToMic ──写入──▶ CABLE Input (VB-Audio)
                                │ 虚拟声卡内部回环
                                ▼
                        CABLE Output ←── 其他软件选它当麦克风
```

物理扬声器的播放路径完全独立，转发只是复制一份系统声的副本。

## 前置要求

- Windows 10 / 11（64-bit）。
- 安装免费虚拟声卡 [VB-Cable](https://vb-audio.com/Cable/)（下载后运行 `VBCABLE_Setup_x64.exe`，管理员身份安装，完成后重启）。

## 快速开始

### 方式一：使用 exe（免安装）

1. 从 Release 下载 `SpeakerToMic.exe`。
2. 双击运行（无窗口，任务管理器中可见 `SpeakerToMic.exe` 进程）。
3. 在目标软件的麦克风列表选择 `CABLE Output (VB-Audio Virtual Cable)`。

### 方式二：从源码运行

```bash
python -m pip install -r requirements.txt
python src/speaker_to_mic.py
```

## 命令行参数

| 参数 | 默认 | 说明 |
| --- | --- | --- |
| `--gain` | `1.0` | 转发音量增益 |
| `--source` | 跟随默认输出 | 指定要采集的播放设备名（模糊匹配） |
| `--cable` | `VB-Audio` | 虚拟声卡写入端名称关键字 |

示例：

```bash
python src/speaker_to_mic.py --gain 1.2 --source "扬声器 (USB Audio Device)"
```

## 设置开机自启（任务计划程序）

PowerShell（管理员可选）：

```powershell
$exe = "C:\路径\SpeakerToMic.exe"
$action  = New-ScheduledTaskAction -Execute $exe
$trigger  = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Seconds 0)
Register-ScheduledTask -TaskName "SpeakerToMic" -Action $action -Trigger $trigger -Settings $settings -Force
```

停用 / 恢复：

```powershell
Disable-ScheduledTask  -TaskName SpeakerToMic   # 停用
Enable-ScheduledTask   -TaskName SpeakerToMic   # 恢复
```

## 从源码打包 exe

在仓库根目录运行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build_exe.ps1
```

产物位于 `dist/SpeakerToMic.exe`。等价 PyInstaller 命令：

```bash
pyinstaller --noconfirm --onefile --noconsole --name SpeakerToMic src/speaker_to_mic.py
```

## 常见问题

- **对方听不到声音？** 确认已安装 VB-Cable、目标软件麦克风选的是 `CABLE Output`，并查看日志 `speaker_to_mic.log` 是否报设备未检测到。
- **自己听的声音变小或被切走？** 本工具为只读回环，不会发生；若出现请检查是否其他音频路由软件（如 VoiceMeeter）改了默认设备。
- **切换了默认播放设备？** 工具重连后自动跟随新的默认输出。

## 许可证

[MIT](LICENSE)
