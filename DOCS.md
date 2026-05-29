# Virtual Doorlock System (VDS) — App 文档

麦驰可视对讲门禁系统的 Home Assistant App，将实体室内机虚拟化，实现对讲、监控、远程解锁等功能。

## 功能

- 虚拟室内机运行与监听
- 门口机呼叫监听与弹窗提醒
- 视频实时监控
- 远程解锁
- 通话接听与挂断

## 安装

1. 在 Home Assistant 中，进入 **设置 → 应用 → 应用商店**
2. 点击右上角菜单 → **仓库**
3. 添加仓库地址：`https://github.com/CelerPi/HA-UpperCoast-DoorLock-Addon`
4. 商店刷新后，找到 **Virtual Doorlock System (VDS)** 并安装

## 配置

安装完成后，在应用的 **配置** 标签页中填写以下参数：

| 参数 | 说明 | 示例 |
|------|------|------|
| `building_id` | 楼栋标识 | `1A` |
| `local_id` | 本地设备ID | `00010116010` |
| `local_ip` | 本机IP地址 | `192.168.16.64` |
| `api_host` | API监听地址 | `0.0.0.0` |
| `api_port` | API监听端口 | `8099` |
| `api_token` | API访问令牌 | （可选） |
| `custom_device_overrides` | 自定义号机覆盖 | `01:192.168.16.224` |

> **默认网络参数说明**：中心地址（`192.168.16.2`）和物业中心机地址（`192.168.16.3`）为本小区固定值，已内置在代码中，无需在配置页填写。如果你的小区网络环境不同，请手动编辑 `app/vds/config.py` 中的 `DEFAULT_CENTER_IP` 和 `DEFAULT_PROPERTY_CENTER_IP` 常量。

## API 接口

App 启动后会提供以下 HTTP 接口：

| 接口 | 方法 | 说明 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/api/status` | GET | 运行时状态和配置 |
| `/api/frame` | GET | 获取当前 JPEG 视频帧 |
| `/api/unlock` | POST | 解锁门口机 |
| `/api/answer` | POST | 接听呼叫 |
| `/api/hangup` | POST | 挂断通话 |

## 注意事项

- 本 App 使用 **主机网络模式**，需要在 HA 主机上绑定 UDP `10000` 和 `10008` 端口
- 当前仅支持 **麦驰可视对讲门禁系统**
- 支持架构：`aarch64`、`amd64`
