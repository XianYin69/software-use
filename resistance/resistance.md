# resistance（约束库 / 兜底）

software-use 不可逾越的红线与执行期降级策略。

## 内容

- [红线约束.md](红线约束.md)：契约 §8 五条红线（私有不外泄 / 无证据不称学会 /
  只追加 / 写盘边界 / 不自判读语义）。
- [降级策略.md](降级策略.md)：`E_NOT_LEARNED` / `E_LEAK` / `E_NO_EVIDENCE` 的兜底动作。

## 遵守原则

1. 违反红线的操作不得执行，除非有显式兜底方案覆盖并留逻辑链。
2. 本目录变更须记入 [CHANGELOG.md](../CHANGELOG.md)。
3. 附属技能各自的 `resistance/私有约束.md` 不得比本目录更宽松。
