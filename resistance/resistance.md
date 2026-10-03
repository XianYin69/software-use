# resistance（约束库 / 兜底）
software-use 不可逾越的红线与执行期降级策略。
## 内容
- [红线约束.md](红线约束.md)：契约 §8 八条红线（注册强制·发布只进私有仓 / 无证据不称学会 /
  只追加 / 写盘与入库边界 / 不自判读语义 / 不绕安全闸 / 不自研输入模拟 / 只引用不复制）。
- [降级策略.md](降级策略.md)：`E_NOT_REGISTERED` / `E_LEAK_TO_PUBLIC` / `E_NO_PRIVATE_REPO` /
  `E_VISIBILITY_MISMATCH` / `E_NO_REMOTE` / `E_NO_EVIDENCE` 的兜底动作。
## 遵守原则
1. 违反红线的操作不得执行，除非有显式兜底方案覆盖并留逻辑链。
2. 本目录变更须记入 [CHANGELOG.md](../CHANGELOG.md)。
3. 附属技能各自的 `resistance/私有约束.md` 不得比本目录更宽松。
4. 「不公开」只能实现为**仓库可见性 PRIVATE**（`su_publish.py --check-visibility` 校验），
   不得实现为「不入库」——后者违反 Skill_Generator git工作流约束第 7 条。
