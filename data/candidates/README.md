# 候选资料层

这里保存尚未进入正式规范化数据的候选字段。候选记录必须带来源、可信度和审核状态，前端不会直接加载本目录。

## 文件

- `episodes.json`：动画集候选字段。
- `entities.json`：人物、组织、案件、地点、道具和篇章候选字段。
- `catalog.json`：电影、特殊电影和 OVA 候选字段。

## 记录协议

```json
{
  "candidateId": "candidate-example-001",
  "targetId": "episode-0001",
  "field": "summary",
  "value": "候选值",
  "sourceRefs": ["source-id"],
  "confidence": "high",
  "reviewStatus": "pending",
  "reviewNote": "待字段级核对"
}
```

允许的 `confidence`：`high`、`medium`、`low`。

允许的 `reviewStatus`：`pending`、`accepted`、`rejected`。

候选层不修改 `data/raw/`，也不直接修改 `data/episodes/episodes.json`。只有审核映射脚本明确应用后，候选值才可以进入正式数据。
