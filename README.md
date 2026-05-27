# 云海湾门禁卡片

![version](https://img.shields.io/badge/version-v0.1.5-blue)
![hacs](https://img.shields.io/badge/hacs-default-orange)
![ha-version](https://img.shields.io/badge/HA-2024.11.0%2B-41BDF5)

云海湾虚拟门禁系统的 Home Assistant Lovelace 自定义卡片，复刻虚拟室内机界面。

## 功能

- 显示门口机列表（4列网格布局）
- 楼层色彩条区分楼层
- 门口机状态指示（在线/离线/当前呼叫中）
- 呼入弹窗（自动弹出）：显示视频画面 + 解锁/接听/挂断按钮
- 主动监控弹窗：点击门口机进入实时监控

## 安装

1. HACS → 仪表盘 → 右下角 → **自定义仓库**
2. 填入仓库地址：`https://github.com/CelerPi/HA-UpperCoast-DoorLock-System`
3. 类别选择：**仪表盘**
4. 搜索并下载 `云海湾门禁卡片`

## 使用

在 Lovelace 仪表盘中添加卡片，选择 `云海湾门禁卡片`。

### 配置选项

```yaml
type: custom:doorlock-card
building_id: building_1_a  # 可选，默认 building_1_a
```

### 楼栋 ID

| ID | 楼栋 |
|----|------|
| building_1_a | 1栋A座 |
| building_1_b | 1栋B座 |
| building_1_c | 1栋C座 |
| building_1_d | 1栋D座 |
| building_1_e | 1栋E座 |
| building_2_a | 2栋A座 |
| building_2_b | 2栋B座 |
| building_2_c | 2栋C座 |

## 依赖

- Home Assistant 2024.11.0+
- 已安装 `uppercoast_doorlock` 集成
- 已安装 `uppercoast_doorlock` Addon