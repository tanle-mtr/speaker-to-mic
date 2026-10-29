#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
speaker_to_mic.py —— 把系统默认扬声器正在播放的声音，经 VB-Cable 转发为一个
虚拟麦克风输入（其他软件在麦克风列表里选 "CABLE Output" 即可听到系统声）。

无界面、后台常驻、异常自动重连。一般无需任何参数，全部自动匹配。

可选参数：
    --gain 1.0          音量增益(默认1.0)
    --source "设备名"   指定要采集的播放设备，默认跟随系统默认输出
    --cable "VB-Audio"  虚拟声卡写入端名称关键字
日志：脚本所在目录 speaker_to_mic.log
依赖：pyaudiowpatch, sounddevice, numpy
"""
import argparse
import sys
import time
import traceback
import os
from datetime import datetime

import numpy as np
import sounddevice as sd
import pyaudiowpatch as pyaudio

def _app_dir() -> str:
    # 打包成 exe 后写到 exe 所在目录；源码运行时写到脚本所在目录
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


LOG_PATH = os.path.join(_app_dir(), "speaker_to_mic.log")


def log(msg: str) -> None:
    line = "[%s] %s" % (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), msg)
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def _hostapi_name(idx: int) -> str:
    return sd.query_hostapis(sd.query_devices()[idx]["hostapi"])["name"]


def find_cable_render(keyword: str = "VB-Audio"):
    """找虚拟声卡写入端（渲染端点），优先 WASAPI，排除 CABLE Output 捕获端。"""
    order = ["Windows WASAPI", "MME", "Windows DirectSound"]
    devs = sd.query_devices()
    for api in order:
        for idx, d in enumerate(devs):
            n = d["name"]
            if (keyword.lower() in n.lower() and d["max_output_channels"] > 0
                    and "cable output" not in n.lower()):
                if _hostapi_name(idx) == api:
                    return idx, n
    return None, None


def pick_loopback(pya: pyaudio.PyAudio, source):
    """返回 (loopback_device_index, rate, channels)。source 为空则跟随默认输出。"""
    if not source:
        lb = pya.get_default_wasapi_loopback()
        if lb:
            return lb["index"], int(lb["defaultSampleRate"]), lb["maxInputChannels"]
    for i in range(pya.get_device_count()):
        d = pya.get_device_info_by_index(i)
        if not d.get("isLoopbackDevice"):
            continue
        if source.lower() in d["name"].lower():
            return i, int(d["defaultSampleRate"]), d["maxInputChannels"]
    return None, None, None


def forward_once(args) -> None:
    pya = pyaudio.PyAudio()
    lb_idx, sr, ch = pick_loopback(pya, args.source)
    if lb_idx is None:
        raise RuntimeError("找不到可采集的播放设备回环: %s" % args.source)

    cable_idx, cable_name = find_cable_render(args.cable)
    if cable_idx is None:
        raise RuntimeError("未检测到虚拟声卡写入端，请先安装 VB-Cable")

    log("采集 loopback#%d @%dHz/%dch -> 虚拟声卡 #%d %s" % (lb_idx, sr, ch, cable_idx, cable_name))

    try:
        lb_name = pya.get_device_info_by_index(lb_idx)["name"]
    except Exception:
        lb_name = "?"

    stream = pya.open(
        format=pyaudio.paInt16,
        channels=ch,
        rate=sr,
        input=True,
        input_device_index=lb_idx,
    )
    out = sd.OutputStream(
        device=cable_idx, samplerate=sr, channels=2, dtype="float32", blocksize=0
    )
    out.start()
    last_check = time.time()
    try:
        while True:
            now = time.time()
            if now - last_check >= 30:
                last_check = now
                # 默认输出可能被切换/设备重枚举，旧 loopback 句柄会静音，
                # 检测到漂移即抛异常触发重连
                try:
                    cur = pya.get_default_wasapi_loopback()
                    cur_key = (cur["index"], cur["name"]) if cur else None
                except Exception:
                    cur_key = None
                if cur_key != (lb_idx, lb_name):
                    log("默认输出已变化 %s -> %s，重建流" % (lb_name, cur_key))
                    raise RuntimeError("loopback drift: 默认输出切换")
            raw = stream.read(1024, exception_on_overflow=False)
            frames = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
            if ch == 2:
                frames = frames.reshape(-1, 2)
            else:
                frames = np.repeat(frames.reshape(-1, 1), 2, axis=1)
            out.write(frames * args.gain)
    finally:
        try:
            stream.stop_stream(); stream.close()
        except Exception:
            pass
        try:
            out.stop(); out.close()
        except Exception:
            pass
        try:
            pya.terminate()
        except Exception:
            pass


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gain", type=float, default=1.0)
    ap.add_argument("--source", default=None)
    ap.add_argument("--cable", default="VB-Audio")
    args = ap.parse_args()

    log("=== speaker_to_mic 启动 ===")
    while True:
        try:
            forward_once(args)
        except Exception:
            log("会话异常，3秒后重连:\n" + traceback.format_exc())
            time.sleep(3)


if __name__ == "__main__":
    main()
