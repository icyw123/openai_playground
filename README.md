# AkShare 日线回测框架

> 本项目由 ChatGPT Codex 自动生成。

该仓库提供一个轻量级的日线回测框架，能够通过 [AkShare](https://akshare.akfamily.xyz/) 获取市场数据，并在上证指数的交易日历上执行策略。示例中包含一个动量策略，用于展示如何编写自定义策略逻辑。

## 核心特性

- 使用 AkShare 抓取指数与个股行情数据。
- 按照指数的每个交易日触发策略逻辑。
- 提供投资组合抽象，跟踪现金与持仓。
- 支持基于目标权重的持仓决策（`hold`、`调仓`、`开仓`、`平仓`）。
- 以**下一根日线的开盘价**对持仓进行盯市，计算当日浮动盈亏。
- 借助 [Pydantic](https://docs.pydantic.dev/) 校验框架数据结构，并通过 [Typer](https://typer.tiangolo.com/) 提供命令行入口。
- 自动保存账户净值随时间变化的图表。

## 环境安装

```bash
pip install -r requirements.txt
```

或直接安装所需依赖：

```bash
pip install akshare matplotlib pandas pydantic typer
```

## 运行示例回测

```bash
python run_backtest.py run --start 20220101 --end 20221231 \
    --index-symbol sh000001 --universe-index 000300 \
    --initial-capital 1000000 --lookback 60 --top-n 3
```

脚本会在控制台输出账户净值曲线的末几行，并将曲线保存到 `backtest_equity_curve.png`。动量策略会根据参数 `--universe-index` 自动获取候选股票，因此无需在入口命令中单独列出股票池。

## 自定义策略

1. 继承 `backtest.strategy.Strategy` 并实现 `on_date` 方法。
2. 使用 `StrategyContext` 访问历史价格数据和当前投资组合快照。
3. 返回由目标权重描述的 `Order` 列表。
4. 将自定义策略交给 `Backtester`，调用 `run()` 启动回测。

更多细节可参考 `backtest/momentum.py` 示例实现。
