---
name: "slides"
description: "Create strategic HTML presentations with Chart.js, design tokens, responsive layouts, and copywriting formulas. Invoke for marketing presentations, pitch decks, and data-driven slides."
---

# Slides

Strategic HTML presentation design with data visualization.

## When to Use

- Marketing presentations and pitch decks
- Data-driven slides with Chart.js
- Strategic slide design with layout patterns
- Copywriting-optimized presentation content

## References

| Topic | File |
|-------|------|
| Creation Guide | `references/create.md` |
| Layout Patterns | `references/layout-patterns.md` |
| HTML Template | `references/html-template.md` |
| Copywriting Formulas | `references/copywriting-formulas.md` |
| Slide Strategies | `references/slide-strategies.md` |

## Requirements

**ALL slides MUST:**
1. Import design-tokens.css - single source of truth
2. Use CSS variables: `var(--color-primary)`, `var(--slide-bg)`
3. Use Chart.js for charts (NOT CSS-only bars)
4. Include navigation (keyboard arrows, click, progress bar)
5. Center align content
6. Focus on persuasion/conversion

## Chart.js Integration

```html
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<canvas id="revenueChart"></canvas>
<script>
new Chart(document.getElementById('revenueChart'), {
    type: 'line',
    data: {
        labels: ['Sep', 'Oct', 'Nov', 'Dec'],
        datasets: [{
            data: [5, 12, 28, 45],
            borderColor: '#FF6B6B',
            backgroundColor: 'rgba(255, 107, 107, 0.1)',
            fill: true,
            tension: 0.4
        }]
    }
});
</script>
```

## Integration

For slide search and generation scripts, use the `design-system` skill which provides:
- `scripts/search-slides.py` - BM25 slide search
- `data/slide-*.csv` - Decision system data files