'use client'

import { Suspense, useState, useEffect } from 'react'
import { useSearchParams } from 'next/navigation'
import AppHeader from '@/shared/components/AppHeader'
import PhaseCard from '@/shared/components/PhaseCard'
import Spinner from '@/shared/components/Spinner'
import { getAnalysisDatePhases } from '@/shared/lib/api'
import { formatShortDate } from '@/shared/lib/dateUtils'
import type { Phase } from '@/shared/lib/types'
import type { RiskLevel } from '@/shared/components/RiskBadge'

function phaseScore(phase: Phase): number {
  const days = phase.end_day - phase.start_day + 1
  const totalMm = phase.assessment?.precipitation?.total_mm?.mean
  if (totalMm == null) return 50
  return Math.min(100, Math.round((totalMm / (days * 2)) * 100))
}

function phaseRisk(score: number): RiskLevel {
  if (score >= 70) return 'excelente'
  if (score >= 50) return 'bom'
  if (score >= 30) return 'atencao'
  return 'alto'
}

function phaseColor(risk: RiskLevel): string {
  if (risk === 'excelente') return '#22c55e'
  if (risk === 'bom') return '#3b82f6'
  if (risk === 'atencao') return '#f59e0b'
  return '#ef4444'
}

function CicloContent() {
  const searchParams = useSearchParams()
  const analysisId = searchParams.get('analysis_id') ?? ''
  const date = searchParams.get('date') ?? ''
  const cropId = searchParams.get('crop_id') ?? ''
  const cropName = searchParams.get('crop_name') ?? 'Crop'

  const [phases, setPhases] = useState<Phase[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!analysisId || !date) return
    getAnalysisDatePhases(analysisId, date)
      .then((res) => setPhases(res.phases))
      .catch(() => setError('Failed to load cycle phases.'))
      .finally(() => setLoading(false))
  }, [analysisId, date])

  const shortDate = date ? formatShortDate(date) : ''
  const previsaoBack = `/previsao?analysis_id=${analysisId}&crop_id=${cropId}&crop_name=${encodeURIComponent(cropName)}&date=${date}`

  return (
    <>
      <AppHeader
        title="Crop Cycle"
        subtitle={`${cropName} — starting ${shortDate}`}
        backHref={previsaoBack}
      />

      <main className="flex-1 flex flex-col gap-2.5 bg-[#f3f4f6] px-4 py-6 overflow-y-auto">

        {loading ? (
          <div className="flex flex-col items-center gap-3 py-16">
            <Spinner />
            <span className="text-[13px] text-[#6b7280]">Loading cycle…</span>
          </div>
        ) : error ? (
          <p className="text-[13px] text-[#c01b1b] bg-[#ffebeb] rounded-lg px-3 py-2">{error}</p>
        ) : phases.length === 0 ? (
          <p className="text-[14px] text-[#6b7280] text-center py-8">
            No phases available for this analysis.
          </p>
        ) : (
          <>
            {phases.map((phase) => {
              const score = phaseScore(phase)
              const risk = phaseRisk(score)
              const color = phaseColor(risk)
              const tempMean = phase.assessment?.temperature_mean?.mean_c?.mean
              const precipTotal = phase.assessment?.precipitation?.total_mm?.mean
              const metrics = [
                { label: 'Temp.', value: tempMean != null ? `${Math.round(tempMean)}°C` : '—' },
                { label: 'Precip.', value: precipTotal != null ? `${Math.round(precipTotal)}mm` : '—' },
              ]

              return (
                <PhaseCard
                  key={phase.id}
                  name={phase.name}
                  duration={`Days ${phase.start_day + 1}–${phase.end_day + 1}`}
                  status={risk}
                  progressPercent={score}
                  progressColor={color}
                  metrics={metrics}
                />
              )
            })}

            <div className="h-2" />

            <a
              href="/"
              className="w-full bg-[#0e8038] text-white py-3.5 px-5 rounded-xl text-[15px] font-semibold leading-none text-center block transition active:scale-[0.97]"
            >
              New analysis
            </a>
          </>
        )}
      </main>
    </>
  )
}

export default function CicloPage() {
  return (
    <Suspense
      fallback={
        <div className="flex-1 flex items-center justify-center">
          <Spinner />
        </div>
      }
    >
      <CicloContent />
    </Suspense>
  )
}
