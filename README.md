[查看Benchmark异常检测报告](output/anomaly_report.md)

## 简介

此项目是一个基于 Python3 的批处理 Pipeline 异常检测系统，用于对历史 Pipeline Metrics 进行中心化的异常分析。

支持：

- Runtime 异常检测
- Volume 异常检测
- Confidence Drift 检测
- YAML 配置化
- Detector 插件化扩展
- Markdown 异常报告输出

适用于：

- Argo Workflow
- 离线 Batch Pipeline
- 数据治理 / 稳定性监控场景

## 技术设计方案

[查看技术设计方案文档](数据%20Pipeline%20异常检测方案.md)

## 关键目录结构说明

- detectors 存放已支持的异常分类检测逻辑
- benchmark 存放基准测试数据集
- output 异常检测报告的输出目录

## 开发环境搭建

### 1. 创建 Python 虚拟环境

```
python -m venv venv
```

### 2. 激活虚拟环境

#### MacOS / Linux

```
source venv/bin/activate
```

#### Windows

```
venv\\Scripts\\activate
```

### 3. 安装依赖

```
pip install -r requirements.txt
```

## 执行

执行异常检测：

```
python main.py
```

## 输入文件

输入文件：

```
benchmark/pipeline_metrics.csv
```

Schema：

| Field          | Description         |
| -------------- | ------------------- |
| batch_id       | Pipeline Batch ID   |
| start_time     | Batch Start Time    |
| end_time       | Batch End Time      |
| input_count    | Input Record Count  |
| output_count   | Output Record Count |
| avg_confidence | Average Confidence  |

## 输出异常检测报告

输出文件：

```
output/anomaly_report.md
```

报告内容包括：

- 异常统计汇总
- 异常类型分布
- Severity 分布
- 异常明细列表

## 配置

配置文件：

```
config/config.yaml
```

支持：

- Detector 开关
- 阈值调整
- Sliding Window 配置
- IQR 参数配置