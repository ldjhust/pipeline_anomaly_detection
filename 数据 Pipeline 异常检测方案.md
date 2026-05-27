# 1. 背景

Maxinsights 当前基于 Argo Workflow 调度离线数据 Pipeline，每天处理数千个数据批次。

随着 Pipeline 数量与数据规模增长，历史运行中逐渐出现以下典型问题：

| 异常类型         | 典型现象                | 风险               |
| ---------------- | ----------------------- | ------------------ |
| Runtime 异常     | 处理耗时显著增长        | SLA 超时、资源阻塞 |
| Volume 异常      | 输出数据量异常减少      | 数据缺失、结果错误 |
| Confidence Drift | avg_confidence 明显偏移 | 模型退化、数据漂移 |

当前主要依赖人工排查，存在：

- 异常发现滞后
- 缺少统一治理机制
- 无法建立历史基线
- 缺少标准化异常报告

因此，需要构建一个：

> 面向离线 Pipeline 的中心化异常检测模块

用于统一分析历史运行数据、自动识别异常批次，并输出标准化异常报告。

# 2. 设计目标

| 目标             | 描述                          |
| ---------------- | ----------------------------- |
| 自动异常检测     | 自动识别异常批次              |
| 多异常类型支持   | Runtime / Volume / Confidence |
| 中心化治理       | 基于历史全局数据分析          |
| 插件化扩展       | 支持新增 Detector             |
| 配置化规则       | 支持动态阈值与算法配置        |
| 与 Workflow 解耦 | 不侵入业务 DAG                |
| 标准化报告       | 输出统一 anomaly_report       |

# 3. 整体架构

系统采用：**“Pipeline 执行” 与 “异常检测” 解耦** 的中心化治理架构

## 3.1 架构图

```
+------------------------------------------------------+
|                Pipeline 调度执行流程                 |
+------------------------------------------------------+

        +--------------------------+
        |  Business Pipeline DAG   |
        +--------------------------+
                     |
                     v
        +--------------------------+
        |  Batch Processing Tasks  |
        +--------------------------+
                     |
                     | Metrics Export
                     v
        +--------------------------+
        |  Metrics Collector       |
        +--------------------------+
                     |
                     v
        +--------------------------+
        | Historical Metrics Store |
        |   (CSV / DB / S3)        |
        +--------------------------+


+------------------------------------------------------+
|              Pipeline 异常检测流程                   |
+------------------------------------------------------+

        +--------------------------+
        | Detection Scheduler      |
        +--------------------------+
                     |
                     v
        +--------------------------+
        | Detection Engine         |
        +--------------------------+
           |          |         |
           v          v         v

    +-------------+ +-------------+ +------------------+
    | Runtime     | | Volume      | | Confidence Drift |
    | Detector    | | Detector    | | Detector         |
    +-------------+ +-------------+ +------------------+

                     |
                     v
        +--------------------------+
        | Anomaly Report Generator |
        +--------------------------+
                     |
                     v
        +--------------------------+
        | anomaly_report.csv       |
        +--------------------------+
```

## 3.2 核心设计原则

| 原则           | 说明                         |
| -------------- | ---------------------------- |
| 执行与检测解耦 | Workflow 仅负责 Metrics 上报 |
| 中心化分析     | 基于全局历史数据建立基线     |
| 插件化设计     | 不同异常类型独立 Detector    |
| 配置化规则     | 支持动态阈值与算法调整       |
| 工程稳定性优先 | 优先采用统计方法             |

# 4. Metrics 上报数据模型

## 4.1 Schema

| 字段           | 类型     | 描述            |
| -------------- | -------- | --------------- |
| batch_id       | string   | 批次 ID         |
| start_time     | datetime | 开始时间        |
| end_time       | datetime | 结束时间        |
| input_count    | int      | 输入数据量      |
| output_count   | int      | 输出数据量      |
| avg_confidence | float    | 平均 confidence |

## 4.2 衍生指标

| 指标             | 计算方式                   |
| ---------------- | -------------------------- |
| duration_seconds | end_time - start_time      |
| output_ratio     | output_count / input_count |

# 5. 异常分类与检测算法

| 异常类型         | 检测指标                   | 检测算法              | 检测逻辑             | 典型风险           |
| ---------------- | -------------------------- | --------------------- | -------------------- | ------------------ |
| Runtime Anomaly  | duration_seconds           | IQR                   | 检测运行耗时异常增长 | SLA 超时、资源阻塞 |
| Volume Anomaly   | output_count、output_ratio | IQR + Ratio Detection | 检测输出量异常下降   | 数据缺失、结果错误 |
| Confidence Drift | avg_confidence             | Sliding Window Drift  | 检测 confidence 漂移 | 模型退化、数据漂移 |

## 5.1 Runtime Anomaly

基于 IQR（Interquartile Range）检测运行时长异常：

$IQR = Q3 - Q1$

$Lower = Q1 - 1.5 \times IQR$

$Upper = Q3 + 1.5 \times IQR$

超出正常区间则判定异常。

## 5.2 Volume Anomaly

同时检测：

- output_count
- output_ratio

其中：

$output\_ratio = \frac{output\_count}{input\_count}$

避免仅基于 output_count 导致误判。

## 5.3 Confidence Drift

基于滑动窗口建立动态基线：

- rolling mean
- rolling std

若：

$|x - \mu| > k\sigma$

则判定发生 Drift。

默认参数：

| 参数          | 默认值 |
| ------------- | ------ |
| window_size   | 10     |
| std_threshold | 2.5    |

# 6. 配置化与插件化设计

## 6.1 Detector 插件化

```python
class BaseDetector:

    def detect(self, df):
        pass
```

当前实现：

* RuntimeIQRDetector
* VolumeDetector
* ConfidenceDriftDetector

## 6.2 YAML 配置化

```yaml
runtime:
  enabled: true
  iqr_multiplier: 1.5

volume:
  enabled: true

confidence:
  enabled: true
  window_size: 10
  std_threshold: 2.5
```

支持：

- 动态阈值调整
- Detector 独立调优

# 7. Pipeline 集成方式

系统采用： “Metrics Export + Centralized Detection” 模式。

## Argo Workflow 负责：

- Pipeline 执行
- Metrics 上报

## Detection 负责：

- 历史数据聚合
- 异常检测
- 报告生成

采用独立部署和定时触发的策略进行定时离线检测对应时间范围内的 Pipeline 执行情况。

# 8. 异常报告设计

输出：anomaly_report.csv

## 报告字段

| 字段            | 描述     |
| --------------- | -------- |
| batch_id        | 批次 ID  |
| anomaly_type    | 异常类型 |
| metric_name     | 指标名称 |
| actual_value    | 实际值   |
| expected_lower  | 正常下限 |
| expected_upper  | 正常上限 |
| deviation_score | 偏差程度 |
| severity        | 告警等级 |

## 输出示例

| batch_id   | anomaly_type     | metric_name      | actual_value | severity |
| ---------- | ---------------- | ---------------- | ------------ | -------- |
| batch_1024 | runtime_anomaly  | duration_seconds | 3800         | critical |
| batch_2048 | confidence_drift | avg_confidence   | 0.42         | warning  |

# 9. 工程实现规划

## 9.1 目录结构

```
pipeline_anomaly_detection/

├── config/
├── data/
├── detectors/
├── engine/
├── utils/
├── output/
├── detect.py
└── requirements.txt
```

## 9.2 技术栈

| 技术    | 用途     |
| ------- | -------- |
| Python3 | 主语言   |
| pandas  | 数据处理 |
| numpy   | 数值计算 |
| pyyaml  | 配置读取 |

## 9.3 核心流程

```
Load Metrics
    ->
Build Features
    ->
Run Detectors
    ->
Merge Anomalies
    ->
Generate Report
```

# 10. 总结

本方案构建了一个：

> 面向数据 Pipeline 的中心化异常检测模块

核心特点：

- Pipeline 执行与异常检测解耦
- 基于历史数据建立动态基线
- 插件化 Detector 架构
- 配置化规则管理
- 易于与 Argo Workflow 集成

适合作为：

> Pipeline 数据质量治理体系的基础能力模块。