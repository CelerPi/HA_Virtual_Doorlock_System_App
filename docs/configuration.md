# 配置说明

## Add-on Options

| 字段 | 示例 | 说明 |
| --- | --- | --- |
| `local_ip` | `192.168.16.64` | HA 主机在门禁网络中的 IP。必须真实存在于 HA 网卡上。 |
| `local_id` | `00010116010` | 虚拟室内机 ID。当前 1601 使用此值。 |
| `building_id` | `building_1_a` | 楼栋预设。当前只有 1 栋 A 座门口机 IP 已知。 |
| `center_ip` | `192.168.16.2` | 小区中心地址。 |
| `property_center_ip` | `192.168.23.255` | 物业中心机地址。 |

## 楼栋 ID

当前内置楼栋：

```text
building_1_a -> 1栋A座
building_1_b -> 1栋B座
building_1_c -> 1栋C座
building_1_d -> 1栋D座
building_1_e -> 1栋E座
building_2_a -> 2栋A座
building_2_b -> 2栋B座
building_2_c -> 2栋C座
```

只有 `building_1_a` 已内置门口机 IP，其余楼栋会生成 8 个空 IP 占位。空 IP 不会参与监听。

## 1 栋 A 座门口机

| 号机 | IP | 楼层 | 位置 |
| --- | --- | --- | --- |
| 1号机 | `192.168.16.224` | 1层 | 车库 |
| 2号机 | `192.168.16.225` | 2层 | 花园 |
| 3号机 | `192.168.16.226` | -1层 | 车库 |
| 4号机 | `192.168.16.227` | -2层 | 车库 |
| 5号机 | `192.168.16.228` | -1层 | 电梯左侧小门左边 |
| 6号机 | `192.168.16.229` | -1层 | 电梯左侧小门右边 |
| 7号机 | `192.168.23.164` | -2层 | 电梯左侧小门左边 |
| 8号机 | `192.168.23.165` | 1层 | 电梯正对 |

## 持久化配置文件

Add-on 会写入：

```text
/data/yunhai_config.json
```

这个文件属于 Add-on 数据目录，会随 Add-on 备份。后续 HA Integration 可以通过服务或 API 修改门口机 IP，再由核心后端读取。

当前同步规则：

- `local_ip`、`local_id`、`building_id`、`center_ip`、`property_center_ip` 以 Add-on options 为准。
- `devices` 中已经手动覆盖过的门口机 IP 会保留。
