'use client'

import { useState } from 'react'
import Image from 'next/image'
import Link from 'next/link'
import { SelectField, type SelectOption } from '@/shared/components/SelectField'

const MUNICIPIOS: SelectOption[] = [
  { value: 'campina-grande-pb', label: 'Campina Grande — PB' },
  { value: 'joao-pessoa-pb',    label: 'João Pessoa — PB'    },
  { value: 'recife-pe',         label: 'Recife — PE'         },
  { value: 'fortaleza-ce',      label: 'Fortaleza — CE'      },
  { value: 'natal-rn',          label: 'Natal — RN'          },
  { value: 'mossoro-rn',        label: 'Mossoró — RN'        },
  { value: 'sobral-ce',         label: 'Sobral — CE'         },
  { value: 'caruaru-pe',        label: 'Caruaru — PE'        },
]

const CULTURAS: SelectOption[] = [
  { value: 'milho',    label: 'Milho'    },
  { value: 'soja',     label: 'Soja'     },
  { value: 'feijao',   label: 'Feijão'   },
  { value: 'algodao',  label: 'Algodão'  },
  { value: 'arroz',    label: 'Arroz'    },
  { value: 'sorgo',    label: 'Sorgo'    },
]

/* Stats are keyed by município value. */
const STATS: Record<string, { temp: string; precip: string; diasSecos: number; nome: string }> = {
  'campina-grande-pb': { temp: '26°C', precip: '587mm', diasSecos: 214, nome: 'CAMPINA GRANDE' },
  'joao-pessoa-pb':    { temp: '28°C', precip: '1842mm', diasSecos: 112, nome: 'JOÃO PESSOA'   },
  'recife-pe':         { temp: '27°C', precip: '2489mm', diasSecos: 92,  nome: 'RECIFE'        },
  'fortaleza-ce':      { temp: '28°C', precip: '1430mm', diasSecos: 180, nome: 'FORTALEZA'     },
  'natal-rn':          { temp: '27°C', precip: '1570mm', diasSecos: 160, nome: 'NATAL'         },
  'mossoro-rn':        { temp: '28°C', precip: '671mm',  diasSecos: 230, nome: 'MOSSORÓ'       },
  'sobral-ce':         { temp: '29°C', precip: '840mm',  diasSecos: 210, nome: 'SOBRAL'        },
  'caruaru-pe':        { temp: '24°C', precip: '641mm',  diasSecos: 195, nome: 'CARUARU'       },
}

export default function InicioPage() {
  const [municipio, setMunicipio] = useState('campina-grande-pb')
  const [cultura, setCultura]     = useState('milho')

  const stats = STATS[municipio]

  return (
    <>
      {/* ── Header ───────────────────────────────────── */}
      <header className="bg-[#1b4132] flex flex-col gap-1.5 px-5 pt-5 pb-6 shrink-0">
        <div className="flex items-center gap-2">
          <div className="size-6 relative shrink-0">
            <Image src="/icons/logo.svg" alt="ClimaRaiz" fill className="object-contain" />
          </div>
          <span className="text-white text-[20px] font-bold leading-none">ClimaRaiz</span>
        </div>
        <p className="text-[13px] text-[rgba(34,197,94,0.75)] leading-none">
          Planejamento agrícola com dados climáticos
        </p>
      </header>

      {/* ── Content ──────────────────────────────────── */}
      <main className="flex-1 flex flex-col gap-4 bg-[#f3f4f6] px-4 py-6 overflow-y-auto">

        {/* Title + description */}
        <h1 className="text-[18px] font-semibold leading-snug text-[#111827]">
          Quando plantar?
        </h1>
        <p className="text-[14px] text-[#6b7280] leading-5">
          Use dados climáticos históricos para encontrar as melhores janelas de plantio.
        </p>

        {/* Selects */}
        <SelectField
          label="MUNICÍPIO"
          options={MUNICIPIOS}
          value={municipio}
          onChange={setMunicipio}
          iconSrc="/icons/pin.svg"
        />
        <SelectField
          label="CULTURA"
          options={CULTURAS}
          value={cultura}
          onChange={setCultura}
          iconSrc="/icons/milho.svg"
        />

        {/* Spacer */}
        <div className="h-2" />

        {/* CTA */}
        <Link
          href="/janelas"
          className="w-full bg-[#0e8038] text-white py-3.5 px-5 rounded-xl text-[15px] font-semibold leading-none active:opacity-90 transition-opacity text-center block"
        >
          Iniciar
        </Link>

        {/* Climate stats */}
        <p className="type-label text-[#9ca3af]">
          DADOS CLIMÁTICOS — {stats.nome}
        </p>

        <div className="flex gap-2">
          <StatCard value={stats.temp}           valueColor="#f59e0b" label="Temp. média" />
          <StatCard value={stats.precip}         valueColor="#3b82f6" label="Precip."     />
          <StatCard value={String(stats.diasSecos)} valueColor="#6b7280" label="Dias secos" />
        </div>
      </main>
    </>
  )
}

/* ── StatCard ──────────────────────────────────────────── */
function StatCard({
  value,
  valueColor,
  label,
}: {
  value: string
  valueColor: string
  label: string
}) {
  return (
    <div className="flex-1 bg-white border border-[#e5e7eb] rounded-[10px] px-3 py-2.5 flex flex-col gap-0.5">
      <span className="text-base font-bold leading-none" style={{ color: valueColor }}>
        {value}
      </span>
      <span className="text-[10px] text-[#9ca3af] leading-none">{label}</span>
    </div>
  )
}
