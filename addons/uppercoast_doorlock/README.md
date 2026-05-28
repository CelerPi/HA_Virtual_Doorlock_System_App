# 虚拟门禁系统

此应用将实体的室内可视对讲机虚拟化，使其在HA中运行、并较为完整的实现了对讲、监控、解锁等实用服务。
当前仅支持的可视对讲品牌：麦驰可视对讲门禁系统。
当前版本从 Home Assistant 应用的配置页读取参数，并常驻监听门禁协议。

由于门禁协议需要在 HA 主机网络上绑定 UDP `10000` 和 `10008`，本应用使用主机网络模式。

## 接口列表

| 接口 | 方法 | 说明 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/api/status` | GET | 运行时状态和配置 |
| `/api/frame` | GET | 获取当前 JPEG 视频帧 |
| `/api/unlock` | POST | 解锁门口机 |
| `/api/answer` | POST | 接听呼叫 |
| `/api/hangup` | POST | 挂断通话 |
| `/api/audio` | GET | 获取接收到的音频 PCM 数据（参数：`?since=audio_id`） |
| `/api/audio` | POST | 发送音频 PCM 数据到门口机 |
| `/api/monitor/start` | POST | 开始主动监控指定门口机 |
| `/api/monitor/stop` | POST | 停止主动监控 |

## 音频格式

音频采样参数为 **8kHz / 单声道 / 16-bit little-endian PCM**。

- `GET /api/audio` 返回 `{"ok": true, "audio_id": N, "chunks": [{"id": N, "pcm": "base64"}]}`，每个 chunk 是一段 PCM 数据。
- `POST /api/audio` 请求体为 `{"target_ip": "...", "pcm": "base64..."}`，PCM 数据需为偶数字节长度。
