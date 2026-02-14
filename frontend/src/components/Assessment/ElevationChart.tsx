import type { GradientAnalysis } from "../../hooks/useAssessment"

interface Props {
  gradient: GradientAnalysis
}

export default function ElevationChart({ gradient }: Props) {
  if (!gradient.steep_segments.length) {
    return (
      <div className="p-3 bg-green-50 dark:bg-green-950/30 rounded-lg text-sm text-green-700 dark:text-green-300">
        <p className="font-medium">Elevation Profile</p>
        <p>Flat approach — max {gradient.max_gradient_pct}% gradient</p>
      </div>
    )
  }

  return (
    <div className="p-3 bg-muted/50 rounded-lg">
      <p className="font-medium text-foreground text-sm mb-2">Steep Segments</p>
      <div className="space-y-1">
        {gradient.steep_segments.map((seg, i) => {
          const color = seg.gradient_pct > 8 ? "bg-red-400 dark:bg-red-500" : "bg-amber-400 dark:bg-amber-500"
          const width = Math.min(100, (seg.gradient_pct / 15) * 100)
          return (
            <div key={i} className="flex items-center gap-2 text-xs">
              <span className="w-20 text-muted-foreground">{seg.start_m}-{seg.end_m}m</span>
              <div
                className="flex-1 bg-muted rounded-full h-3"
                role="progressbar"
                aria-valuenow={seg.gradient_pct}
                aria-valuemin={0}
                aria-valuemax={15}
                aria-label={`Gradient ${seg.gradient_pct}%`}
              >
                <div className={`${color} rounded-full h-3`} style={{ width: `${width}%` }} />
              </div>
              <span className="w-12 text-right font-medium text-foreground">{seg.gradient_pct}%</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
