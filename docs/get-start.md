# Get Start

本文说明如何把本仓库作为 Home Assistant Add-on 仓库安装，并让 HA 主机接入云海湾门禁网络。

## 文档目录

- [安装 Add-on](#安装-add-on)
- [基础配置](configuration.md)
- [网络连接方式](network.md)
- [排障](troubleshooting.md)

## 当前状态

当前 Add-on 已具备后端常驻核心：

- 读取 HA Add-on options。
- 维护持久化配置文件 `/data/yunhai_config.json`。
- 绑定 UDP `10000` 和 `10008`。
- 监听已配置门口机呼入。
- 识别呼入触发包 `cd000100`、`98000100`、`b7000100`。
- 呼叫会话中发送接听、解锁和音频上行包。
- 解析呼叫/监控视频分片并重组 JPEG。

Lovelace 卡片和 HA Custom Integration 还未完成，因此当前阶段主要用于验证 Add-on 后端在 HA 设备上能常驻运行。

## 安装 Add-on

1. 在 Home Assistant 中打开 **Settings > Add-ons > Add-on Store**。
2. 右上角菜单选择 **Repositories**。
3. 添加仓库地址：

   ```text
   https://github.com/CelerPi/HA-UpperCoast-DoorLock-System.git
   ```

4. 刷新 Add-on Store，打开 **Yunhai Intercom**。
5. 点击 **Install**。
6. 进入 **Configuration** 页，按 [基础配置](configuration.md) 填写参数。
7. 打开 **Start on boot** 和 **Watchdog**。
8. 点击 **Start**。
9. 在 **Log** 页确认看到 `yunhai_intercom_started`。

## 最小可用配置

1 栋 A 座默认配置如下：

```yaml
local_ip: "192.168.16.64"
local_id: "00010116010"
building_id: "building_1_a"
center_ip: "192.168.16.2"
property_center_ip: "192.168.23.255"
```

如果 HA 主机实际 IP 不是 `192.168.16.64`，必须把 `local_ip` 改成 HA 主机在门禁网段上的真实地址。

## 第一次启动后会发生什么

Add-on 会创建：

```text
/data/yunhai_config.json
```

这个文件保存当前门口机列表和 IP。Add-on options 中的本机 IP、本机 ID、楼栋、中心地址会在每次启动时同步到该文件；门口机 IP 覆盖值会保留。

## 验证方式

1. 确认 Add-on 日志没有端口占用或本机 IP 绑定失败。
2. 在门口机上呼叫当前房号。
3. 后端会在内存中进入呼叫会话，并按旧原型已验证流程发送会话保活和视频请求。
4. 如果后续接入 HA Integration 或调试接口，可调用解锁/接听服务验证 `b7000600` 和 `b7000500`。

当前后端遵循旧 `Unlock` 原型中已经真实验证过的会话流程，但去掉了本地 Web UI、命令行实验分支和浏览器打开逻辑。
