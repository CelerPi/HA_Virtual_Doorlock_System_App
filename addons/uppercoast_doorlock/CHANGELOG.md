# 更新日志

## 0.1.0 - 2026-05-27

- 初始发布：Home Assistant Addon 版本
- 将应用目录、应用标识和 Python 包名统一为 `uppercoast_doorlock`
- 加载项名称：虚拟门禁系统
- 当前仅支持麦驰可视对讲门禁系统
- 楼栋下拉选项为中文楼栋名，保存并重启后加载对应门口机配置
- 启动日志输出为中文摘要，不再输出完整 JSON 配置
- 配置页、应用说明、使用文档均使用中文命名
- 提供 `/health`、`/api/status`、`/api/frame`、`/api/unlock`、`/api/answer`、`/api/hangup` 等 HTTP 接口
