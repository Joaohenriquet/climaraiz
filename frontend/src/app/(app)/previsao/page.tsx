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
  if (pct == null) return { text: 'Sem avaliação disponível', label: 'Sem dados', color: '#6b7280' }
  if (pct >= 70) return { text: 'Sua data é excelente', label: 'Favorável', color: '#16a34a' }
  if (pct >= 50) return { text: 'Boa escolha de data', label: 'Bom', color: '#16a34a' }
  if (pct >= 30) return { text: 'Atenção para esta data', label: 'Atenção', color: '#da8003' }
  return { text: 'Data desfavorável historicamente', label: 'Alto risco', color: '#c01b1b' }
}


function PrevisaoContent() {
  const searchParams = useSearchParams()
  const analysisId = searchParams.get('analysis_id') ?? ''
  const date = searchParams.get('date') ?? ''
  const cropId = searchParams.get('crop_id') ?? ''
  const cropName = searchParams.get('crop_name') ?? 'Cultura'

  const [data, setData] = useState<AnalysisDate & { crop_id: number; analysis_id: string } | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!analysisId || !date) return
    getAnalysisDate(analysisId, date)
      .then(setData)
      .catch(() => setError('Erro ao carregar previsão.'))
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
        title="Previsão de Plantio"
        subtitle={`${cropName} — ${shortDate}`}
        backHref={janelasBack}
      />

      <main className="flex-1 flex flex-col gap-4 items-center bg-[#f3f4f6] px-4 py-6 overflow-y-auto">

        {loading ? (
          <div className="flex flex-col items-center gap-3 py-16">
            <Spinner />
            <span className="text-[13px] text-[#6b7280]">Carregando previsão…</span>
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
                  Em {Math.round(pct)}% dos anos históricos, esta data atendeu a todos os critérios
                  climáticos configurados para {cropName}.
                </p>
              ) : (
                <p className="text-[13px] text-[#6b7280] text-center leading-[18px] max-w-[310px]">
                  Não há avaliação de cenário disponível para esta data.
                </p>
              )}
            </div>

            <a
              href={`/ciclo?${headerParams}`}
              className="w-full bg-[#0e8038] text-white py-3.5 px-5 rounded-xl text-[15px] font-semibold leading-none text-center block"
            >
              Ver ciclo da cultura
            </a>

            <div className="w-full bg-[#f3f4f6] border border-[#e5e7eb] flex items-center gap-2.5 px-3.5 py-3 rounded-[10px]">
              <Image src="/icons/info.svg" alt="" width={16} height={16} className="shrink-0" />
              <span className="text-[12px] text-[#6b7280] leading-normal">
                Baseado em 25 anos de dados climáticos históricos (2001–2025) · NASA/MERRA-2.
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
