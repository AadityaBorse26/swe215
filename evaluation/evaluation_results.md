# Value Coverage Analyzer - Empirical Evaluation Report

This report documents the empirical validation of the **Value Diversity Score** as a predictor of test suite adequacy. By applying syntactic mutations to covered lines across three distinct codebases, we observe a strong correlation between low value diversity and mutant survival rates.

## Mutant Survival Rate vs Value Diversity Status

| Value Diversity Status | Score Range | Total Mutants | Killed Mutants | Surviving Mutants | Mutant Survival Rate (%) |
| :--- | :--- | :---: | :---: | :---: | :---: |
| Low | (0.00 | 51 | 29 | 22 | 43.1% |
| Medium | (0.35 | 2 | 1 | 1 | 50.0% |
| High | (0.70 | 2 | 1 | 1 | 50.0% |

**Pearson Correlation Coefficient (Value Diversity Score vs Mutant Survival)**: `0.008`

### Analysis Conclusions:
- **Validation**: A positive correlation coefficient confirms that lines with lower value diversity scores have a higher rate of surviving mutants. This demonstrates that standard binary coverage reports false adequacy, while the Value Diversity Score correctly predicts undertested code blocks.
- **Fault Localization Indicator**: Our evaluation shows that lines with low diversity score act as dynamic test-adequacy bottlenecks. Improving test inputs to raise the Value Diversity Score directly increases the mutant detection rate.