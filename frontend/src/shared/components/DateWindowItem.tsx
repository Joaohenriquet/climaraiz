import Link from 'next/link'
import RiskBadge, { type RiskLevel } from './RiskBadge'

interface DateWindowItemProps {
  date: string
  monthYear: string
  temp: string
  precip: string
  risk: RiskLevel
  selected?: boolean
  href?: string
}

export default function DateWindowItem({
  date,
  monthYear,
  temp,
  precip,
  risk,
  selected = false,
  href,
}: DateWindowItemProps) {
  const cls = [
    'w-full bg-white flex items-center justify-between px-3.5 py-3 rounded-xl text-left transition-colors active:opacity-90',
    selected ? 'border-[1.5px] border-[#16a34a]' : 'border border-[#e5e7eb]',
  ].join(' ')

  const content = (
    <>
      <div className="flex items-center gap-3">
        <div className={`flex items-center justify-center px-2.5 py-2 rounded-lg shrink-0 ${selected ? 'bg-[#1b4132]' : 'bg-[#f3f4f6]'}`}>
          <span className={`text-[13px] font-bold leading-none ${selected ? 'text-white' : 'text-[#111827]'}`}>
            {date}
          </span>
        </div>

        <div className="flex flex-col gap-0.5">
          <span className="text-[13px] font-medium text-[#111827] leading-none">{monthYear}</span>
          <div className="flex items-center gap-1.5 text-[12px] text-[#6b7280]">
            <span>{temp}</span>
            <span className="text-[#d1d5db]">·</span>
            <span>{precip}</span>
          </div>
        </div>
      </div>

      <RiskBadge risk={risk} />
    </>
  )

  if (href) return <Link href={href} className={cls}>{content}</Link>
  return <div className={cls}>{content}</div>
}
