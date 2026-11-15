'use client'

import { useRef, useState, useEffect } from 'react'
import Image from 'next/image'

export interface SelectOption {
  value: string
  label: string
}

interface SelectFieldProps {
  label: string
  options: SelectOption[]
  value: string
  onChange: (value: string) => void
  iconSrc: string
}

export function SelectField({ label, options, value, onChange, iconSrc }: SelectFieldProps) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const onPointerDown = (e: PointerEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('pointerdown', onPointerDown)
    return () => document.removeEventListener('pointerdown', onPointerDown)
  }, [])

  const selected = options.find((o) => o.value === value)

  return (
    <div className="flex flex-col gap-1.5 w-full">
      {/* Label */}
      <span
        className="type-label"
        style={{ color: 'var(--cr-gray-400)' }}
      >
        {label}
      </span>

      {/* Trigger + Dropdown */}
      <div ref={ref} className="relative">
        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          className="w-full bg-white border border-[#e5e7eb] rounded-xl px-3.5 py-2.5 flex items-center justify-between"
          aria-expanded={open}
          aria-haspopup="listbox"
        >
          {/* Left: icon badge + label */}
          <div className="flex items-center gap-2">
            <span className="bg-[#f0fdf4] p-1.5 rounded-lg flex items-center justify-center">
              <Image src={iconSrc} alt="" width={16} height={16} />
            </span>
            <span
              className="text-[15px] font-semibold"
              style={{ color: 'var(--cr-gray-900)' }}
            >
              {selected?.label ?? 'Selecionar'}
            </span>
          </div>

          {/* Chevron */}
          <Image
            src="/icons/chevron-down.svg"
            alt=""
            width={18}
            height={18}
            className={`transition-transform duration-200 ${open ? 'rotate-180' : ''}`}
          />
        </button>

        {/* Dropdown */}
        {open && (
          <ul
            role="listbox"
            className="absolute left-0 right-0 top-full mt-1 bg-white border border-[#e5e7eb] rounded-xl shadow-lg z-20 overflow-hidden py-1"
          >
            {options.map((opt) => {
              const isActive = opt.value === value
              return (
                <li key={opt.value} role="option" aria-selected={isActive}>
                  <button
                    type="button"
                    onClick={() => { onChange(opt.value); setOpen(false) }}
                    className={`w-full text-left px-4 py-3 text-[14px] transition-colors ${
                      isActive
                        ? 'bg-[#f0fdf4] text-[#15803d] font-semibold'
                        : 'text-[#111827] hover:bg-[#f3f4f6]'
                    }`}
                  >
                    {opt.label}
                  </button>
                </li>
              )
            })}
          </ul>
        )}
      </div>
    </div>
  )
}
