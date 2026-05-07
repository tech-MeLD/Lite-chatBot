---
name: "ui-styling"
description: "Create beautiful, accessible UIs with shadcn/ui (Radix UI + Tailwind), Tailwind CSS utility styling, and canvas-based visual designs. Invoke when building interfaces, implementing design systems, creating responsive layouts, or adding accessible components."
---

# UI Styling Skill

Comprehensive skill for creating beautiful, accessible user interfaces combining shadcn/ui components, Tailwind CSS utility styling, and canvas-based visual design systems.

## When to Use

- Building UI with React-based frameworks (Next.js, Vite, Remix, Astro)
- Implementing accessible components (dialogs, forms, tables, navigation)
- Styling with utility-first CSS approach
- Creating responsive, mobile-first layouts
- Implementing dark mode and theme customization
- Building design systems with consistent tokens
- Generating visual designs, posters, or brand materials

## Core Stack

### Component Layer: shadcn/ui
- Pre-built accessible components via Radix UI primitives
- Copy-paste distribution model (components live in your codebase)
- TypeScript-first with full type safety
- Composable primitives for complex UIs

### Styling Layer: Tailwind CSS
- Utility-first CSS framework
- Build-time processing with zero runtime overhead
- Mobile-first responsive design
- Consistent design tokens (colors, spacing, typography)

## Quick Start

**Install shadcn/ui with Tailwind:**
```bash
npx shadcn@latest init
```

**Add components:**
```bash
npx shadcn@latest add button card dialog form
```

**Use components:**
```tsx
import { Button } from "@/components/ui/button"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"

export function Dashboard() {
  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardHeader>
        <CardTitle className="text-2xl font-bold">Analytics</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-muted-foreground">View your metrics</p>
        <Button className="w-full">View Details</Button>
      </CardContent>
    </Card>
  )
}
```

## References

**Component Library**
- `references/shadcn-components.md` - Complete component catalog
- `references/shadcn-theming.md` - Theming and customization
- `references/shadcn-accessibility.md` - Accessibility patterns

**Styling System**
- `references/tailwind-utilities.md` - Core utility classes
- `references/tailwind-responsive.md` - Responsive design
- `references/tailwind-customization.md` - Configuration

**Visual Design**
- `references/canvas-design-system.md` - Design philosophy

## Utility Scripts

**Add shadcn/ui components:**
```bash
python scripts/shadcn_add.py button card dialog
```

**Generate Tailwind config:**
```bash
python scripts/tailwind_config_gen.py --colors brand:blue --fonts display:Inter
```

## Best Practices

1. **Component Composition**: Build complex UIs from simple, composable primitives
2. **Utility-First Styling**: Use Tailwind classes directly
3. **Mobile-First Responsive**: Start with mobile styles, layer responsive variants
4. **Accessibility-First**: Leverage Radix UI primitives, add focus states
5. **Design Tokens**: Use consistent spacing scale, color palettes, typography system
6. **Dark Mode Consistency**: Apply dark variants to all themed elements