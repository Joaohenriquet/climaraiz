'use client'

import { usePathname } from 'next/navigation'
import Image from 'next/image'
import Link from 'next/link'

const TABS = [
  { href: '/',       icon: '/icons/nav-plantio.svg', label: 'Plantio' },
  { href: '/clima',  icon: '/icons/nav-clima.svg',   label: 'Clima'   },
]

export default function BottomNav() {
  const pathname = usePathname()

  return (
    <nav className="bg-[#1b4132] flex items-stretch pt-2.5 pb-7 shrink-0">
      {TABS.map(({ href, icon, label }) => {
        const active = pathname === href

        return (
          <Link
            key={href}
            href={href}
            className="flex flex-1 flex-col items-center gap-1 relative"
            aria-label={label}
          >
            <span
              className={`h-0.5 w-8 rounded-full transition-colors ${
                active ? 'bg-[#22c55e]' : 'bg-transparent'
              }`}
            />
            <Image
              src={icon}
              alt={label}
              width={22}
              height={22}
              className={`transition-opacity ${active ? 'opacity-100' : 'opacity-50'}`}
            />
          </Link>
        )
      })}
    </nav>
  )
}
