# AI模型目录

这个目录用于存放AI模型文件。由于模型文件通常很大，不适合直接提交到代码仓库，因此需要单独下载和管理。

## 支持的模型类型

### 1. 文本分析模型
- **情感分析模型**: 用于分析新闻、公告等文本的情感倾向
- **关键词提取模型**: 提取文本中的关键信息
- **文本分类模型**: 对新闻、研报等进行分类

### 2. 时间序列预测模型
- **LSTM模型**: 用于股价趋势预测
- **Transformer模型**: 用于复杂时间序列分析
- **Prophet模型**: 用于趋势和季节性分析

### 3. 推荐系统模型
- **协同过滤模型**: 基于历史数据的推荐
- **深度学习推荐模型**: 基于神经网络的推荐

## 模型文件结构

建议的目录结构：
```
models/
├── sentiment/          # 情感分析模型
│   ├── bert_sentiment.bin
│   └── config.json
├── prediction/         # 预测模型
│   ├── lstm_price.h5
│   └── transformer_trend.pt
├── recommendation/     # 推荐模型
│   ├── collaborative_filter.pkl
│   └── deep_recommend.onnx
└── pretrained/        # 预训练模型
    ├── chinese_bert/
    └── financial_word2vec/
```

## 模型下载和安装

### 方法1: 手动下载
1. 从模型提供方下载模型文件
2. 将模型文件放置到对应的子目录中
3. 更新配置文件中的模型路径

### 方法2: 脚本下载
```bash
# 运行模型下载脚本（需要实现）
python scripts/download_models.py
```

### 方法3: 云存储同步
```bash
# 从云存储同步模型文件（需要配置）
aws s3 sync s3://your-bucket/models/ ./ai/models/
```

## 模型配置

在 `config/settings.py` 中配置模型路径：

```python
AI_MODEL_PATHS = {
    'sentiment_model': './ai/models/sentiment/bert_sentiment.bin',
    'price_prediction': './ai/models/prediction/lstm_price.h5',
    'recommendation': './ai/models/recommendation/collaborative_filter.pkl'
}
```

## 使用说明

1. **开发环境**: 可以使用较小的测试模型进行开发
2. **生产环境**: 使用完整的训练好的模型
3. **模型更新**: 定期更新模型以提高准确性

## 注意事项

- 模型文件不要提交到Git仓库
- 确保模型文件的版本兼容性
- 定期备份重要的模型文件
- 注意模型文件的许可证要求