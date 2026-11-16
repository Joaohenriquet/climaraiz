'use client'

import { Suspense, useState, useEffect, useRef } from 'react'
import { useSearchParams } from 'next/navigation'
import AppHeader from '@/shared/components/AppHeader'
import DateWindowItem from '@/shared/components/DateWindowItem'
import Spinner from '@/shared/components/Spinner'
import { getAnalysis } from '@/shared/lib/api'
import { formatShortDate, formatMonthYear, formatWindowRange } from '@/shared/lib/dateUtils'
import type { Analysis, AnalysisDate, ScenarioAssessment } from '@/shared/lib/types'
import type { RiskLevel } from '@/shared/components/RiskBadge'

function toRiskLevel(assessment: ScenarioAssessment): RiskLevel {
  const pct = assessment?.scenario_criteria_met_pct
  if (pct == null) return 'moderado'
  if (pct >= 70) return 'favoravel'
  if (pct >= 50) return 'bom'
  if (pct >= 30) return 'atencao'
  return 'alto'
}

function formatTemp(date: AnalysisDate): string {
  const mean = date.historical_assessment?.temperature_mean?.mean_c?.mean
  if (mean == null) return '—'
  return `${Math.round(mean)}°C`
}

function formatPrecip(date: AnalysisDate): string {
  const total = date.historical_assessment?.precipitation?.total_mm?.mean
  if (total == null) return '—'
  return `${Math.round(total)}mm`
}

function JanelasContent() {
  const searchParams = useSearchParams()
  const analysisId = searchParams.get('analysis_id') ?? ''
  const cropId = searchParams.get('crop_id') ?? ''
  const cropName = searchParams.get('crop_name') ?? 'Cultura'

  const [analysis, setAnalysis] = useState<Analysis | null>(null)
  const [error, setError] = useState<string | null>(null)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    if (!analysisId) return

    async function poll() {
      try {
        const result = await getAnalysis(analysisId)
        setAnalysis(result)
        if (result.status === 'completed' || result.status === 'failed') {
          if (intervalRef.current) clearInterval(intervalRef.current)
        }
      } catch {
        setError('Erro ao buscar análise.')
        if (intervalRef.current) clearInterval(intervalRef.current)
      }
    }

    poll()
    intervalRef.current = setInterval(poll, 2500)
    return () => { if (intervalRef.current) clearInterval(intervalRef.current) }
  }, [analysisId])

  const isLoading = !analysis || analysis.status === 'processing'
  const isFailed = analysis?.status === 'failed'
  const dates = analysis?.status === 'completed' ? (analysis.dates ?? []) : []

  const window = analysis?.window
  const rangeLabel = window ? formatWindowRange(window.start_date, window.end_date) : ''

  const headerParams = `analysis_id=${analysisId}&crop_id=${cropId}&crop_name=${encodeURIComponent(cropName)}`

  return (
    <>
      <AppHeader
        title="Janelas de Plantio"
        subtitle={`${cropName} em Campina Grande — PB`}
        backHref="/"
      />

      <main className="flex-1 flex flex-col gap-2 bg-[#f3f4f6] px-4 py-6 overflow-y-auto">

        {isLoading && !isFailed && (
          <div className="flex flex-col items-center gap-4 py-16">
            <Spinner />
            <div className="flex flex-col items-center gap-1">
              <span className="text-[14px] font-semibold text-[#111827]">
                Analisando janelas de plantio…
              </span>
              {analysis?.progress != null && (
                <span className="text-[12px] text-[#6b7280]">
                  {Math.round(analysis.progress * 100)}% concluído
                </span>
              )}
            </div>
          </div>
        )}

        {isFailed && (
          <div className="bg-[#ffebeb] border border-[#fca5a5] rounded-xl px-4 py-4">
            <p className="text-[14px] font-semibold text-[#c01b1b]">Análise falhou</p>
            <p className="text-[13px] text-[#6b7280] mt-1">
              {analysis?.error?.message ?? 'Tente novamente a partir da tela inicial.'}
            </p>
          </div>
        )}

        {error && (
          <p className="text-[13px] text-[#c01b1b] bg-[#ffebeb] rounded-lg px-3 py-2">{error}</p>
        )}

        {dates.length > 0 && (
          <>
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[15px] font-semibold text-[#111827]">Janelas de plantio</span>
              <span className="text-[13px] text-[#6b7280]">{rangeLabel}</span>
            </div>

            {dates.map((d) => (
              <DateWindowItem
                key={d.date}
                date={formatShortDate(d.date)}
                monthYear={formatMonthYear(d.date)}
                temp={formatTemp(d)}
                precip={formatPrecip(d)}
                risk={toRiskLevel(d.scenario_assessment)}
                href={`/previsao?${headerParams}&date=${d.date}`}
              />
            ))}
          </>
        )}
      </main>
    </>
  )
}

export default function JanelasPage() {
  return (
    <Suspense
      fallback={
        <div className="flex-1 flex items-center justify-center">
          <Spinner />
        </div>
      }
    >
      <JanelasContent />
    </Suspense>
  )
}
