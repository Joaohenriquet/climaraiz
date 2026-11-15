interface CircularProgressProps {
  value: number          // 0–100
  label: string          // text under percentage, e.g. "Favorável"
  labelColor?: string
  size?: number          // px, default 140
  strokeWidth?: number   // px, default 10
  trackColor?: string
  progressColor?: string
}

export default function CircularProgress({
  value,
  label,
  labelColor = '#16a34a',
  size = 140,
  strokeWidth = 10,
  trackColor = '#e5e7eb',
  progressColor = '#16a34a',
}: CircularProgressProps) {
  const r = (size - strokeWidth) / 2
  const cx = size / 2
  const cy = size / 2
  const circumference = 2 * Math.PI * r
  const offset = circumference * (1 - Math.min(100, Math.max(0, value)) / 100)

  return (
    <div className="relative shrink-0" style={{ width: size, height: size }}>
      <svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        style={{ transform: 'rotate(-90deg)' }}
      >
        {/* Track */}
        <circle
          cx={cx}
          cy={cy}
          r={r}
          fill="none"
          stroke={trackColor}
          strokeWidth={strokeWidth}
        />
        {/* Progress arc */}
        <circle
          cx={cx}
          cy={cy}
          r={r}
          fill="none"
          stroke={progressColor}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ transition: 'stroke-dashoffset 0.6s ease' }}
        />
      </svg>

      {/* Center text */}
      <div className="absolute inset-0 flex flex-col items-center justify-center gap-0.5">
        <span className="text-[28px] font-bold leading-none text-[#111827]">
          {value}%
        </span>
        <span className="text-[12px] leading-none" style={{ color: labelColor }}>
          {label}
        </span>
      </div>
    </div>
  )
}
