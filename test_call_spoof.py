#!/usr/bin/env python3
"""
============================================================
麦驰可视对讲 - 门口机呼入测试脚本 (Scapy 伪造源 IP 版)
============================================================

功能：模拟门口机呼叫室内机，测试 Home Assistant 能否弹出呼叫弹窗。

原理：
  使用 scapy 伪造 UDP 包的源 IP 为真实门口机 IP，绕过 Addon 的源 IP 校验。
  无需修改 Addon 配置，无需注册 MacBook IP。

网络要求：
  - MacBook 和 HA 主机在同一个二层网络（同一交换机/VLAN）
  - 因为伪造源 IP 需要操作系统支持，MacBook 必须能直接访问目标网段

安装依赖：
  pip3 install scapy

用法：
  sudo python3 test_call_spoof.py

注意：
  - 必须使用 sudo（root 权限），否则 scapy 无法伪造源 IP
  - 如果 HA 主机和 MacBook 之间有路由器做源 IP 校验（如 ACL），伪造会失败
============================================================
"""

import argparse
import base64
import socket
import struct
import sys
import time

# ============================================================
# 协议常量
# ============================================================
TARGET_PORT = 10000
DISCOVERY_PORT = 10008
PENGUIN_HEADER = b"PENGUIN0"

# 呼叫触发命令字（与 call_state.py 中的 CALL_TRIGGER_COMMANDS 一致）
CALL_TRIGGERS = {
    "cd": bytes.fromhex("cd000100"),
    "98": bytes.fromhex("98000100"),
    "b7": bytes.fromhex("b7000100"),
}
CALL_END = bytes.fromhex("b4000600")

# 测试 JPEG（320x240 黑色）
TEST_JPEG = base64.b64decode(
    "/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEB"
    "AQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEB"
    "AQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEB"
    "AQEBAQH/wAARCAHgAcADASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAn/xAAU"
    "EAEAAAAAAAAAAAAAAAAAAAAA/8QAFAEBAAAAAAAAAAAAAAAAAAAAAP/EABQRAQAAAAAA"
    "AAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCf/9k="
)


def send_packet_scapy(payload, src_ip, src_port, dst_ip, dst_port):
    """使用 scapy 发送伪造源 IP 的 UDP 包。"""
    try:
        from scapy.all import IP, UDP, Raw, send
    except ImportError:
        print("错误: 未安装 scapy。请执行: pip3 install scapy")
        sys.exit(1)
    packet = IP(src=src_ip, dst=dst_ip) / UDP(sport=src_port, dport=dst_port) / Raw(payload)
    send(packet, verbose=0)


def build_penguin_packet(command_hex, payload_length, device_id, device_ip, local_id, local_ip, extra=b""):
    def text_to_hex(s): return s.encode("ascii").hex()
    def ip_to_hex(s): return socket.inet_aton(s).hex()
    def word_hex(n): return n.to_bytes(2, "little").hex()

    payload_hex = "".join([
        "50454e4755494e30", command_hex, "0000", word_hex(payload_length),
        "0" * 32,
        text_to_hex(device_id), "0" * 16, ip_to_hex(device_ip),
        text_to_hex(f"S{local_id}"), "0" * 16, ip_to_hex(local_ip),
    ])
    return bytes.fromhex(payload_hex) + extra


def build_identity_payload(local_id):
    device_id = f"S{local_id}".encode("ascii")
    return b"\x02" + device_id + bytes(35 - 1 - len(device_id))


def build_cd_payload():
    return bytes.fromhex(
        "50454e4755494e30" "cd000200" "00002000" "00000000000000000000000000000000"
    )


def build_session_info_payload(local_ip, local_id):
    def text_to_hex(s): return s.encode("ascii").hex()
    def ip_to_hex(s): return socket.inet_aton(s).hex()
    def word_hex(n): return n.to_bytes(2, "little").hex()
    payload_hex = "".join([
        "50454e4755494e30", "98000200", "0000", word_hex(898),
        "0" * 32, "0100", text_to_hex(f"S{local_id}"),
        "0000000000000000", ip_to_hex(local_ip),
    ])
    payload = bytes.fromhex(payload_hex)
    return payload + bytes(898 - len(payload))


def send_discovery(target_ip, local_id, door_ip):
    payload = build_identity_payload(local_id)
    send_packet_scapy(payload, door_ip, DISCOVERY_PORT, target_ip, DISCOVERY_PORT)
    print(f"  [发现] 身份包 {door_ip}:{DISCOVERY_PORT} -> {target_ip}:{DISCOVERY_PORT}")


def send_trigger(cmd, device_id, door_ip, local_id, local_ip, target_ip):
    pkt = build_penguin_packet(cmd.hex(), 80, device_id, door_ip, local_id, local_ip)
    send_packet_scapy(pkt, door_ip, TARGET_PORT, target_ip, TARGET_PORT)
    print(f"  [呼叫] 触发包 {cmd.hex()} {door_ip}:{TARGET_PORT} -> {target_ip}:{TARGET_PORT}")


def send_video_frame(device_id, door_ip, local_id, local_ip, target_ip, jpeg):
    hdr = struct.pack("<HHHHH", 1, 1, 1, 1, len(jpeg))
    pkt = build_penguin_packet("b7000a00", 90 + len(jpeg), device_id, door_ip, local_id, local_ip, hdr + jpeg)
    send_packet_scapy(pkt, door_ip, TARGET_PORT, target_ip, TARGET_PORT)


def send_audio(device_id, door_ip, local_id, local_ip, target_ip, pcm):
    hdr = struct.pack("<HHHHH", 3, 1, 1, 1, len(pcm))
    pkt = build_penguin_packet("b7000a00", 90 + len(pcm), device_id, door_ip, local_id, local_ip, hdr + pcm)
    send_packet_scapy(pkt, door_ip, TARGET_PORT, target_ip, TARGET_PORT)


def main():
    parser = argparse.ArgumentParser(description="模拟门口机呼叫室内机（伪造源 IP 版）")
    parser.add_argument("--target", default="192.168.16.64", help="Addon 的 local_ip（HA 主机 IP）")
    parser.add_argument("--local-id", default="00010116010", help="Addon 的 local_id")
    parser.add_argument("--door-ip", default="192.168.16.224", help="真实门口机 IP（用于伪造源 IP）")
    parser.add_argument("--door-no", default="01", help="门口机编号")
    parser.add_argument("--duration", type=int, default=30, help="呼叫持续时间（秒）")
    parser.add_argument("--trigger", choices=["cd", "98", "b7"], default="cd", help="触发命令字")
    args = parser.parse_args()

    target_ip = args.target
    local_id = args.local_id
    door_ip = args.door_ip
    door_no = args.door_no
    duration = args.duration
    trigger_cmd = CALL_TRIGGERS[args.trigger]
    device_id = f"M000101{door_no}000"
    local_ip = target_ip

    print("=" * 60)
    print("  麦驰可视对讲 - 门口机呼入测试 (Scapy 伪造源 IP)")
    print("=" * 60)
    print(f"\n  目标 HA 主机:  {target_ip}")
    print(f"  室内机 ID:     {local_id}")
    print(f"  伪造门口机 IP: {door_ip} (真实门口机 IP)")
    print(f"  门口机编号:    {door_no}")
    print(f"  触发命令:      {trigger_cmd.hex()}")
    print(f"  持续时间:      {duration} 秒")
    print()

    # 检查 scapy
    try:
        from scapy.all import IP, UDP, Raw, send
        print("[检查] scapy 已安装 ✓")
    except ImportError:
        print("[检查] scapy 未安装，请先执行: pip3 install scapy")
        sys.exit(1)

    # 检查权限（macOS 上需要 root）
    if sys.platform != "win32":
        import os
        if os.getuid() != 0:
            print("[警告] 当前不是 root 用户。伪造源 IP 通常需要 sudo 权限。")
            print("       如果测试失败，请用 sudo 运行: sudo python3 test_call_spoof.py")
            print()
            confirm = input("是否继续尝试？(y/N): ").strip().lower()
            if confirm != "y":
                sys.exit(0)

    print("\n[阶段 1] 发送身份发现包...")
    send_discovery(target_ip, local_id, door_ip)
    time.sleep(0.5)

    print(f"\n[阶段 2] 发送呼叫触发包 ({trigger_cmd.hex()})...")
    for i in range(3):
        send_trigger(trigger_cmd, device_id, door_ip, local_id, local_ip, target_ip)
        time.sleep(0.3)

    print(f"\n[阶段 3] 开始模拟视频流（持续 {duration} 秒）...")
    print("         Home Assistant 应该弹出「呼入中」弹窗")
    print("         按 Ctrl+C 提前结束\n")

    pcm = b"\x00" * 512
    frame_no = 0
    try:
        while frame_no < duration * 2:
            frame_no += 1
            elapsed = frame_no * 0.5

            send_video_frame(device_id, door_ip, local_id, local_ip, target_ip, TEST_JPEG)
            send_audio(device_id, door_ip, local_id, local_ip, target_ip, pcm)

            print(f"\r  [视频] 帧 #{frame_no}  ({elapsed:.1f}s/{duration}s)", end="", flush=True)
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass

    print(f"\n\n[阶段 4] 发送挂断包...")
    end_pkt = build_penguin_packet("b4000600", 80, device_id, door_ip, local_id, local_ip)
    send_packet_scapy(end_pkt, door_ip, TARGET_PORT, target_ip, TARGET_PORT)
    print("         呼叫结束")

    print("\n" + "=" * 60)
    print("  测试完成")
    print("=" * 60)
    print("\n检查 Home Assistant:")
    print("  1. Dashboard 卡片应弹出「呼入中」弹窗")
    print("  2. 显示 1号机 视频画面")
    print("  3. 有「接听」「解锁」「挂断」按钮")
    print("  4. 点击「接听」后视频继续")
    print()


if __name__ == "__main__":
    main()
