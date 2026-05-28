# 云海湾门禁系统 — Home Assistant Addon

![version](https://img.shields.io/badge/version-v0.1.0-blue)
![ha-version](https://img.shields.io/badge/HA-2024.11.0%2B-41BDF5)

麦驰可视对讲门禁系统的 Home Assistant Addon，将实体室内机虚拟化，实现对讲、监控、远程解锁等功能。

## 功能

- 虚拟室内机运行与监听
- 门口机呼叫监听与弹窗提醒
- 视频实时监控
- 远程解锁
- 通话接听与挂断

## 安装

1. 在 Home Assistant 中，进入 **设置 → 加载项 → 加载项商店**
2. 点击右上角菜单 → **仓库**
3. 添加仓库地址：`https://github.com/CelerPi/HA-UpperCoast-DoorLock-Addon`
4. 商店刷新后，找到 **虚拟门禁系统** 并安装

## 配置

安装完成后，在加载项的 **配置** 标签页中填写以下参数：

| 参数 | 说明 | 示例 |
|------|------|------|
| `building_id` | 楼栋标识 | `1栋A座` |
| `local_id` | 本地设备ID | `00010116010` |
| `local_ip` | 本机IP地址 | `192.168.16.64` |
| `center_ip` | 管理中心IP | `192.168.16.2` |
| `property_center_ip` | 物业中心IP | `192.168.16.3` |
| `api_host` | API监听地址 | `0.0.0.0` |
| `api_port` | API监听端口 | `8099` |
| `api_token` | API访问令牌 | （可选） |
| `door_01_ip` ~ `door_08_ip` | 门口机IP地址 | `192.168.16.10` |

## API 接口

Addon 启动后会提供以下 HTTP 接口：

| 接口 | 方法 | 说明 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/api/status` | GET | 运行时状态和配置 |
| `/api/frame` | GET | 获取当前 JPEG 视频帧 |
| `/api/unlock` | POST | 解锁门口机 |
| `/api/answer` | POST | 接听呼叫 |
| `/api/hangup` | POST | 挂断通话 |

## 注意事项

- 本 Addon 使用 **主机网络模式**，需要在 HA 主机上绑定 UDP `10000` 和 `10008` 端口
- 当前仅支持 **麦驰可视对讲门禁系统**
- 支持架构：`aarch64`、`amd64`

## 版本日志

详见 [addons/uppercoast_doorlock/CHANGELOG.md](addons/uppercoast_doorlock/CHANGELOG.md)
