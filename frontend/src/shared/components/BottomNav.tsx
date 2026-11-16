'use client'

import { usePathname } from 'next/navigation'
import Link from 'next/link'

function HomeIcon() {
  return (
    <svg width="22" height="22" viewBox="0 0 22 22" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 9.5L11 3L19 9.5V19a1 1 0 0 1-1 1H14v-5h-4v5H4a1 1 0 0 1-1-1Z" />
    </svg>
  )
}

function TrendIcon() {
  return (
    <svg width="22" height="22" viewBox="0 0 22 22" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="3,16 8,10 12,13 17,7" />
      <polyline points="14,7 17,7 17,10" />
    </svg>
  )
}

const TABS = [
  { href: '/',      Icon: HomeIcon,  label: 'Home'   },
  { href: '/clima', Icon: TrendIcon, label: 'Trends' },
]

export default function BottomNav() {
  const pathname = usePathname()

  return (
    <nav className="bg-[#1b4132] flex items-stretch pt-2.5 pb-7 shrink-0">
      {TABS.map(({ href, Icon, label }) => {
        const FLOW_PATHS = ['/janelas', '/previsao', '/ciclo']
        const active = pathname === href || (href === '/' && FLOW_PATHS.some(p => pathname.startsWith(p)))
        return (
          <Link
            key={href}
            href={href}
            className={`flex flex-1 flex-col items-center gap-1 transition-colors ${
              active ? 'text-[#86efac]' : 'text-[#86efac]/40'
            }`}
            aria-label={label}
          >
            <span className={`h-0.5 w-8 rounded-full transition-colors ${active ? 'bg-[#22c55e]' : 'bg-transparent'}`} />
            <Icon />
          </Link>
        )
      })}
    </nav>
  )
}
