'use client'

import { Suspense, useState, useEffect } from 'react'
import Image from 'next/image'
import { useSearchParams } from 'next/navigation'
import AppHeader from '@/shared/components/AppHeader'
import CircularProgress from '@/shared/components/CircularProgress'
import Spinner from '@/shared/components/Spinner'
import { getAnalysisDate } from '@/shared/lib/api'
import { formatShortDate } from '@/shared/lib/dateUtils'
import type { AnalysisDate } from '@/shared/lib/types'

function scoreLabel(pct: number | null): { text: string; label: string; color: string } {
  if (pct == null) return { text: 'No assessment available', label: 'No data', color: '#6b7280' }
  if (pct >= 70) return { text: 'Excellent planting date', label: 'Favorable', color: '#16a34a' }
  if (pct >= 50) return { text: 'Good date choice', label: 'Good', color: '#16a34a' }
  if (pct >= 30) return { text: 'Caution for this date', label: 'Caution', color: '#da8003' }
  return { text: 'Historically unfavorable date', label: 'High risk', color: '#c01b1b' }
}


function PrevisaoContent() {
  const searchParams = useSearchParams()
  const analysisId = searchParams.get('analysis_id') ?? ''
  const date = searchParams.get('date') ?? ''
  const cropId = searchParams.get('crop_id') ?? ''
  const cropName = searchParams.get('crop_name') ?? 'Crop'

  const [data, setData] = useState<AnalysisDate & { crop_id: number; analysis_id: string } | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!analysisId || !date) return
    getAnalysisDate(analysisId, date)
      .then(setData)
      .catch(() => setError('Failed to load forecast.'))
      .finally(() => setLoading(false))
  }, [analysisId, date])

  const pct = data?.scenario_assessment?.scenario_criteria_met_pct ?? null
  const score = pct != null ? Math.round(pct) : 0
  const { text: scoreText, label: scoreLabel_, color: scoreColor } = scoreLabel(pct)

  const shortDate = date ? formatShortDate(date) : ''
  const headerParams = `analysis_id=${analysisId}&crop_id=${cropId}&crop_name=${encodeURIComponent(cropName)}&date=${date}`
  const janelasBack = `/janelas?analysis_id=${analysisId}&crop_id=${cropId}&crop_name=${encodeURIComponent(cropName)}`

  return (
    <>
      <AppHeader
        title="Planting Forecast"
        subtitle={`${cropName} — ${shortDate}`}
        backHref={janelasBack}
      />

      <main className="flex-1 flex flex-col gap-4 items-center bg-[#f3f4f6] px-4 py-6 overflow-y-auto">

        {loading ? (
          <div className="flex flex-col items-center gap-3 py-16">
            <Spinner />
            <span className="text-[13px] text-[#6b7280]">Loading forecast…</span>
          </div>
        ) : error ? (
          <p className="text-[13px] text-[#c01b1b] bg-[#ffebeb] rounded-lg px-3 py-2 w-full">{error}</p>
        ) : (
          <>
            <div className="w-full bg-white border border-[#e5e7eb] rounded-2xl px-4 py-6 flex flex-col gap-4 items-center">
              <CircularProgress
                value={pct != null ? score : 0}
                label={scoreLabel_}
                labelColor={scoreColor}
                progressColor={scoreColor}
              />
              <p className="text-[16px] font-semibold text-[#111827] text-center leading-snug">
                {scoreText}
              </p>
              {pct != null ? (
                <p className="text-[13px] text-[#6b7280] text-center leading-[18px] max-w-[310px]">
                  In {Math.round(pct)}% of historical years, this date met all climate
                  criteria set for {cropName}.
                </p>
              ) : (
                <p className="text-[13px] text-[#6b7280] text-center leading-[18px] max-w-[310px]">
                  No scenario assessment is available for this date.
                </p>
              )}
            </div>

            <a
              href={`/ciclo?${headerParams}`}
              className="w-full bg-[#0e8038] text-white py-3.5 px-5 rounded-xl text-[15px] font-semibold leading-none text-center block transition active:scale-[0.97]"
            >
              View crop cycle
            </a>

            <div className="w-full bg-[#f3f4f6] border border-[#e5e7eb] flex items-center gap-2.5 px-3.5 py-3 rounded-[10px]">
              <Image src="/icons/info.svg" alt="" width={16} height={16} className="shrink-0" />
              <span className="text-[12px] text-[#6b7280] leading-normal">
                Based on 25 years of historical climate data (2001–2025) · NASA/MERRA-2.
              </span>
            </div>
          </>
        )}
      </main>
    </>
  )
}

export default function PrevisaoPage() {
  return (
    <Suspense
      fallback={
        <div className="flex-1 flex items-center justify-center">
          <Spinner />
        </div>
      }
    >
      <PrevisaoContent />
    </Suspense>
  )
}
