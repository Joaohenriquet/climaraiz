import Link from 'next/link'
import Image from 'next/image'
import AppHeader from '@/shared/components/AppHeader'
import CircularProgress from '@/shared/components/CircularProgress'

interface PhaseCardProps {
  value: number
  label: string
  bg: string
  valueColor: string
}

function PhaseCard({ value, label, bg, valueColor }: PhaseCardProps) {
  return (
    <div
      className="flex flex-1 flex-col gap-1 items-center justify-center px-2 py-2.5 rounded-[10px]"
      style={{ backgroundColor: bg }}
    >
      <span className="text-base font-bold leading-none" style={{ color: valueColor }}>
        {value}%
      </span>
      <span className="text-[10px] text-[#6b7280] leading-none">{label}</span>
    </div>
  )
}

export default function PrevisaoPage() {
  return (
    <>
      <AppHeader
        title="Previsão de Plantio"
        subtitle="Milho — 13 de março"
        backHref="/janelas"
      />

      <main className="flex-1 flex flex-col gap-4 items-center bg-[#f3f4f6] px-4 py-6 overflow-y-auto">

        {/* Circular progress card */}
        <div className="w-full bg-white border border-[#e5e7eb] rounded-2xl px-4 py-6 flex flex-col gap-4 items-center">
          <CircularProgress value={86} label="Favorável" />

          <p className="text-[16px] font-semibold text-[#111827] text-center leading-snug">
            Sua data é excelente
          </p>
          <p className="text-[13px] text-[#6b7280] text-center leading-[18px] max-w-[310px]">
            Condições climáticas favoráveis para o ciclo completo do milho nesta data.
          </p>
        </div>

        {/* Phase summary */}
        <div className="flex gap-2 w-full">
          <PhaseCard value={90} label="Germinação" bg="#e0fae7" valueColor="#16a34a" />
          <PhaseCard value={94} label="Floração"   bg="#fef3e0" valueColor="#f59e0b" />
          <PhaseCard value={74} label="Colheita"   bg="#e0fae7" valueColor="#16a34a" />
        </div>

        <div className="h-2" />

        {/* CTA */}
        <Link
          href="/ciclo"
          className="w-full bg-[#0e8038] text-white py-3.5 px-5 rounded-xl text-[15px] font-semibold leading-none text-center block"
        >
          Ver ciclo da cultura
        </Link>

        {/* Info banner */}
        <div className="w-full bg-[#f3f4f6] border border-[#e5e7eb] flex items-center gap-2.5 px-3.5 py-3 rounded-[10px]">
          <Image src="/icons/info.svg" alt="" width={16} height={16} className="shrink-0" />
          <span className="text-[12px] text-[#6b7280] leading-normal">
            Baseado em 20 anos de dados climáticos históricos.
          </span>
        </div>
      </main>
    </>
  )
}
