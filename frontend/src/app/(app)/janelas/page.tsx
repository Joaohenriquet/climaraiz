import AppHeader from '@/shared/components/AppHeader'
import DateWindowItem from '@/shared/components/DateWindowItem'
import { type RiskLevel } from '@/shared/components/RiskBadge'

interface PlantingWindow {
  id: string
  date: string
  monthYear: string
  temp: string
  precip: string
  risk: RiskLevel
}

const WINDOWS: PlantingWindow[] = [
  { id: '15jan', date: '15 jan', monthYear: 'Janeiro 2025',   temp: '27°C', precip: '22mm', risk: 'alto'      },
  { id: '1fev',  date: '1 fev',  monthYear: 'Fevereiro 2025', temp: '27°C', precip: '38mm', risk: 'moderado'  },
  { id: '15fev', date: '15 fev', monthYear: 'Fevereiro 2025', temp: '27°C', precip: '52mm', risk: 'moderado'  },
  { id: '1mar',  date: '1 mar',  monthYear: 'Março 2025',     temp: '26°C', precip: '68mm', risk: 'favoravel' },
  { id: '15mar', date: '15 mar', monthYear: 'Março 2025',     temp: '26°C', precip: '74mm', risk: 'favoravel' },
  { id: '1abr',  date: '1 abr',  monthYear: 'Abril 2025',     temp: '25°C', precip: '88mm', risk: 'favoravel' },
]

export default function JanelasPage() {
  return (
    <>
      <AppHeader
        title="Janelas de Plantio"
        subtitle="Milho em Campina Grande — PB"
        backHref="/"
      />

      <main className="flex-1 flex flex-col gap-2 bg-[#f3f4f6] px-4 py-6 overflow-y-auto">
        <div className="flex items-center justify-between mb-1.5">
          <span className="text-[15px] font-semibold text-[#111827]">Janelas de plantio</span>
          <span className="text-[13px] text-[#6b7280]">Jan–Mar 2025</span>
        </div>

        {WINDOWS.map((w) => (
          <DateWindowItem
            key={w.id}
            date={w.date}
            monthYear={w.monthYear}
            temp={w.temp}
            precip={w.precip}
            risk={w.risk}
            href="/previsao"
          />
        ))}
      </main>
    </>
  )
}
