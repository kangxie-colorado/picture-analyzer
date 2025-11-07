# Risk Analysis Skill

**Purpose**: Analyze Grafana dashboard screenshots to identify potential operational risks and capacity issues.

## Overview

This skill guides Claude to perform comprehensive risk analysis on monitoring dashboards by:
1. Extracting individual panels from dashboard screenshots
2. Analyzing each panel for risk indicators using vision capabilities
3. Generating a detailed risk assessment report

## When to Use This Skill

Use this skill when asked to:
- Analyze dashboard health or identify risks
- Review capacity utilization and potential bottlenecks
- Assess operational metrics for anomalies
- Generate risk reports from monitoring dashboards

## Prerequisites

- Dashboard screenshot image file
- Dashboard configuration in `config/dashboards/<dashboard-name>/`
- `coordinates.yaml` file with panel definitions

## Workflow

### Step 1: Generate Analysis Context

First, use the `analyze-risk` tool to extract panels and generate analysis context:

```bash
./analyze-risk <image-path> <dashboard-name> --output context.yaml
```

This will:
- Extract all panels from the dashboard
- Categorize each panel by type (read/write capacity, storage, QPS, hotkeys, etc.)
- List relevant risk indicators for each panel type
- Save context information to `context.yaml`

**Example**:
```bash
./analyze-risk screenshots/abase-risk-anal-11041203.png abase-risk-analysis-analyzed --output context.yaml
```

### Step 2: Review Analysis Context

Read the generated `context.yaml` to understand:
- Panel IDs and descriptions
- Panel types and their risk indicators
- Paths to extracted panel images

### Step 3: Analyze Each Panel

For each panel listed in the context:

1. **Read the panel image** using the Read tool
2. **Analyze the visualization** based on panel type:

   **For Capacity Panels (Read/Write):**
   - Check current usage vs quota/limit lines
   - Look for values approaching or exceeding thresholds
   - Identify sudden spikes or unusual patterns
   - Check for cross-DC imbalances

   **For Storage Panels:**
   - Assess disk usage percentage
   - Identify tables consuming excessive space
   - Check for rapid growth trends
   - Note remaining capacity

   **For QPS/Quota Panels:**
   - Compare QPS against quota lines
   - Identify quota violations
   - Check for traffic concentration on specific shards

   **For Hotkey Panels:**
   - Identify presence of hot keys
   - Assess RU consumption by top keys
   - Note uneven access patterns

   **For Value Size Panels:**
   - Check for large value sizes
   - Identify values approaching limits
   - Note anomalous patterns per DC

3. **Document findings** for each panel:
   - Current metric values
   - Threshold/limit values
   - Risk level: LOW / MEDIUM / HIGH / CRITICAL
   - Specific concerns or anomalies
   - Recommendations

### Step 4: Generate Risk Report

Create a comprehensive risk report with the following structure:

```yaml
dashboard_analysis:
  dashboard_name: <name>
  analyzed_at: <timestamp>
  image_source: <path>
  overall_risk_level: LOW | MEDIUM | HIGH | CRITICAL

  summary:
    total_panels: <count>
    high_risk_panels: <count>
    critical_issues: <count>

  panels:
    - panel_id: S1-L-read
      description: "读总计 - Global Read RU"
      type: read_capacity
      risk_level: MEDIUM

      current_state:
        current_value: "~750 RU"
        quota_limit: "1000 RU"
        utilization: "75%"

      findings:
        - "Current usage at 75% of quota"
        - "Stable pattern with occasional spikes to 85%"
        - "No immediate capacity concerns"

      risk_indicators:
        - indicator: "Usage approaching quota"
          severity: MEDIUM
          details: "At 75% with spikes to 85%, leaving limited headroom"

      recommendations:
        - "Monitor for continued growth trends"
        - "Consider quota increase if sustained above 80%"

    # ... more panels

  critical_issues:
    - issue: "Write capacity near limit"
      panels: [S1-L-write, S1-R-write]
      severity: HIGH
      description: "Write RU usage consistently above 90% of quota"
      recommendation: "Immediate quota increase required"

  summary_recommendations:
    immediate_actions:
      - "Increase write quota from 1000 to 1500 RU"
      - "Investigate hot key 'user:12345' consuming 35% of RU"

    monitoring_priorities:
      - "Watch disk usage on table 'user_events' (growing at 10GB/day)"
      - "Track QPS patterns for shard 'shard-03' (approaching quota)"

    long_term_considerations:
      - "Consider data archival strategy for high-growth tables"
      - "Evaluate sharding strategy to address hot key issues"
```

### Step 5: Save Report

Save the risk report to a file:

```bash
# The report should be saved as YAML or JSON
# Filename: risk_report_<dashboard>_<timestamp>.yaml
```

## Risk Level Guidelines

**CRITICAL**: Immediate action required
- Metrics exceeding limits/quotas
- Service degradation likely or occurring
- Data loss risk present

**HIGH**: Urgent attention needed
- Metrics at 90%+ of limits
- Rapid growth trends
- Potential service impact within hours/days

**MEDIUM**: Should be addressed soon
- Metrics at 70-90% of limits
- Steady growth toward limits
- Potential issues within days/weeks

**LOW**: Monitoring recommended
- Metrics below 70% of limits
- Stable patterns
- No immediate concerns

## Output Format

The skill should produce:

1. **Analysis Context** (`context.yaml`): Panel metadata and risk indicators
2. **Risk Report** (`risk_report_<timestamp>.yaml`): Detailed findings and recommendations
3. **Console Summary**: High-level overview of critical issues

## Example Usage

```bash
# User request
"Analyze the risk in screenshots/abase-risk-anal-11041203.png"

# Claude workflow
1. Run: ./analyze-risk screenshots/abase-risk-anal-11041203.png abase-risk-analysis-analyzed --output context.yaml
2. Read context.yaml
3. For each panel, read image and analyze metrics
4. Generate comprehensive risk report
5. Save report and present summary
```

## Tips for Accurate Analysis

1. **Read metrics carefully**: Pay attention to units, scales, and time ranges
2. **Compare to thresholds**: Always relate current values to limits/quotas shown
3. **Consider trends**: Look at graph shapes, not just current values
4. **Note legends**: Color coding and legend labels indicate severity
5. **Cross-reference panels**: Related panels (e.g., read/write, global/per-DC) should be analyzed together
6. **Be specific**: Quote actual values from visualizations
7. **Be conservative**: When uncertain, err on the side of flagging for review

## Validation Checklist

Before finalizing the report:

- [ ] All panels from context analyzed
- [ ] Risk levels assigned with justification
- [ ] Specific metric values quoted
- [ ] Recommendations are actionable
- [ ] Critical issues clearly highlighted
- [ ] Report saved to file
- [ ] Summary presented to user

## Notes

- This skill relies on Claude's vision capabilities to read dashboard visualizations
- Accuracy depends on image quality and clarity of metrics
- For production use, validate findings against actual system metrics
- This analysis is advisory; human review is recommended for critical decisions
