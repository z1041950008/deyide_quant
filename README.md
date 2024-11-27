# deyide_quant

张得意量化工具箱

## 简介

这是我的一个量化工具箱，里面包含了一些常用的量化指标，可以用于选股和择时。
后续我的一些想法，会更新到这个工具箱中，敬请期待。

## 功能说明

### 布林带选股策略
- bolling_bands_select_every_work_day_basic_score.py

- 选出符合布林带买入条件的股票
- 标记出符合布林带卖出条件的股票
- 集成简单的评分系统，用于评估股票的基本面信息
  - 打分越高，股票越符合要求

- 使用说明
  - 仅支持日线数据
  - 针对市值前300的股票
  - 经过测算，市值越大的票，布林带策略越适用
  - 直接运行后，会在excel_stock目录下生成一个excel文件，文件名为bolling_bands_select_every_work_day_basic_score.xlsx

### 回测功能

- backtest.py
- boll_screener.py
- 目前只写了一个布林带的回测，后续会更新更多策略的回测
- 用法参考backtest_bolling_bands_new.py
- 回测结果会在html目录下生成一个html文件，文件名为以控制台打印为准
- todo
  - 读取数据需要缓存，读取财务数据需要根据日期来选择报告期
  - 佣金和滑点需要根据实际情况来调整
  - 策略需要抽象优化

## 联系方式

### 微信公众号 : 疯狂量化

![公众号二维码](./image/gongzhonghao.jpg)
### 个人微信
![微信二维码](./image/wechat-zhangdeyi.jpg)