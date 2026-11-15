import Link from 'next/link'
import AppHeader from '@/shared/components/AppHeader'
import PhaseCard from '@/shared/components/PhaseCard'
import { type RiskLevel } from '@/shared/components/RiskBadge'

interface Phase {
  name: string
  duration: string
  status: RiskLevel
  progressPercent: number
  progressColor: string
  metrics: { label: string; value: string }[]
}

const PHASES: Phase[] = [
  {
    name: 'Germinação',
    duration: '1–15 dias',
    status: 'excelente',
    progressPercent: 100,
    progressColor: '#22c55e',
    metrics: [
      { label: 'Temp.',   value: '26°C' },
      { label: 'Precip.', value: '74mm' },
      { label: 'Umid.',   value: '76%'  },
    ],
  },
  {
    name: 'Floração',
    duration: '30–50 dias',
    status: 'excelente',
    progressPercent: 71,
    progressColor: '#f59e0b',
    metrics: [
      { label: 'Temp.',   value: '25°C' },
      { label: 'Precip.', value: '92mm' },
      { label: 'Umid.',   value: '82%'  },
    ],
  },
  {
    name: 'Enchimento do grão',
    duration: '50–90 dias',
    status: 'bom',
    progressPercent: 85,
    progressColor: '#22c55e',
    metrics: [
      { label: 'Temp.',   value: '25°C' },
      { label: 'Precip.', value: '48mm' },
      { label: 'Umid.',   value: '68%'  },
    ],
  },
  {
    name: 'Maturação e colheita',
    duration: '90–125 dias',
    status: 'atencao',
    progressPercent: 76,
    progressColor: '#f59e0b',
    metrics: [
      { label: 'Temp.',   value: '24°C' },
      { label: 'Precip.', value: '22mm' },
      { label: 'Umid.',   value: '56%'  },
    ],
  },
]

export default function CicloPage() {
  return (
    <>
      <AppHeader
        title="Ciclo da Cultura"
        subtitle="Milho — início em 13 de março"
        backHref="/previsao"
      />

      <main className="flex-1 flex flex-col gap-2.5 bg-[#f3f4f6] px-4 py-6 overflow-y-auto">
        {PHASES.map((phase) => (
          <PhaseCard
            key={phase.name}
            name={phase.name}
            duration={phase.duration}
            status={phase.status}
            progressPercent={phase.progressPercent}
            progressColor={phase.progressColor}
            metrics={phase.metrics}
          />
        ))}

        <div className="h-2" />

        <Link
          href="/"
          className="w-full bg-[#0e8038] text-white py-3.5 px-5 rounded-xl text-[15px] font-semibold leading-none text-center block"
        >
          Fazer nova análise
        </Link>
      </main>
    </>
  )
}
