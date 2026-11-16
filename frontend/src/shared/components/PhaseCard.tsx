import RiskBadge, { type RiskLevel } from './RiskBadge'

interface PhaseMetric {
  label: string
  value: string
}

interface PhaseCardProps {
  name: string
  duration: string
  status: RiskLevel
  progressPercent: number
  progressColor: string
  metrics: PhaseMetric[]
}

export default function PhaseCard({
  name,
  duration,
  status,
  progressPercent,
  progressColor,
  metrics,
}: PhaseCardProps) {
  return (
    <div className="bg-white border border-[#e5e7eb] rounded-xl p-3.5 flex flex-col gap-2.5 w-full">
      <div className="flex items-center justify-between">
        <div className="flex flex-col gap-0.5">
          <span className="text-[14px] font-semibold text-[#111827] leading-none">{name}</span>
          <span className="text-[11px] text-[#6b7280] leading-none">{duration}</span>
        </div>
        <RiskBadge risk={status} />
      </div>

      <div className="h-1.5 w-full bg-[#e5e7eb] rounded-full overflow-hidden">
        <div
          className="h-1.5 rounded-full"
          style={{ width: `${Math.min(100, Math.max(0, progressPercent))}%`, backgroundColor: progressColor }}
        />
      </div>

      <div className="flex gap-4">
        {metrics.map((m) => (
          <div key={m.label} className="flex items-center gap-1">
            <span className="text-[11px] text-[#6b7280]">{m.label}</span>
            <span className="text-[12px] font-semibold text-[#111827]">{m.value}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
