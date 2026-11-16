'use client'

import { useState, useEffect } from 'react'
import Image from 'next/image'
import { useRouter } from 'next/navigation'
import { SelectField, type SelectOption } from '@/shared/components/SelectField'
import Spinner from '@/shared/components/Spinner'
import { getCrops, getClimateTrends, createAnalysis } from '@/shared/lib/api'
import { CROP_CONFIGS } from '@/shared/lib/cropConfig'
import { getPlantingYear } from '@/shared/lib/dateUtils'
import type { Crop, TrendsResponse } from '@/shared/lib/types'

const MUNICIPALITY_ID = 2504009

const MUNICIPIO_OPTIONS: SelectOption[] = [
  { value: String(MUNICIPALITY_ID), label: 'Campina Grande — PB' },
]

export default function InicioPage() {
  const router = useRouter()
  const [crops, setCrops] = useState<Crop[]>([])
  const [cropOptions, setCropOptions] = useState<SelectOption[]>([])
  const [trends, setTrends] = useState<TrendsResponse | null>(null)
  const [loadingData, setLoadingData] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [selectedCropId, setSelectedCropId] = useState<string>('')

  useEffect(() => {
    async function loadData() {
      try {
        const [fetchedCrops, fetchedTrends] = await Promise.all([
          getCrops(),
          getClimateTrends(MUNICIPALITY_ID),
        ])
        setCrops(fetchedCrops)
        const options = fetchedCrops.map((c) => ({ value: String(c.id), label: c.name }))
        setCropOptions(options)
        if (options.length > 0) setSelectedCropId(options[0].value)
        setTrends(fetchedTrends)
      } catch {
        setError('Não foi possível conectar ao servidor. Verifique se o backend está rodando.')
      } finally {
        setLoadingData(false)
      }
    }
    loadData()
  }, [])

  async function handleStart() {
    const cropId = Number(selectedCropId)
    if (!cropId) return
    const config = CROP_CONFIGS[cropId]
    if (!config) return

    setError(null)
    try {
      const result = await createAnalysis({
        municipality_id: MUNICIPALITY_ID,
        crop_id: cropId,
        planting_year: getPlantingYear(),
        cycle_days: config.cycle_days,
        historical_period: { start_year: 2001, end_year: 2025 },
        phases: config.phases,
        check_windows: config.check_windows,
      })
      const cropName = crops.find((c) => c.id === cropId)?.name ?? ''
      router.push(
        `/janelas?analysis_id=${result.analysis_id}&crop_id=${cropId}&crop_name=${encodeURIComponent(cropName)}`
      )
    } catch {
      setError('Erro ao iniciar análise. Tente novamente.')
    }
  }

  const tempIndicator = trends?.indicators?.temperature_mean
  const precipIndicator = trends?.indicators?.precipitation

  const tempValue = tempIndicator?.status === 'available' && tempIndicator.mean != null
    ? `${Math.round(tempIndicator.mean)}°C`
    : '—'

  const precipValue = precipIndicator?.status === 'available' && precipIndicator.mean != null
    ? `${Math.round(precipIndicator.mean)}mm`
    : '—'

  const slopeVal = precipIndicator?.trend?.slope_per_decade
  const trendValue = slopeVal != null
    ? `${slopeVal > 0 ? '+' : ''}${Math.round(slopeVal)}mm`
    : '—'
  const trendColor = slopeVal != null && slopeVal > 0 ? '#3b82f6' : '#6b7280'

  return (
    <>
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

      <main className="flex-1 flex flex-col gap-4 bg-[#f3f4f6] px-4 py-6 overflow-y-auto">

        <h1 className="text-[18px] font-semibold leading-snug text-[#111827]">
          Quando plantar?
        </h1>
        <p className="text-[14px] text-[#6b7280] leading-5">
          Use dados climáticos históricos para encontrar as melhores janelas de plantio.
        </p>

        <SelectField
          label="MUNICÍPIO"
          options={MUNICIPIO_OPTIONS}
          value={String(MUNICIPALITY_ID)}
          onChange={() => {}}
          iconSrc="/icons/pin.svg"
        />

        {loadingData ? (
          <div className="bg-white border border-[#e5e7eb] rounded-xl px-3.5 py-3 flex items-center gap-2">
            <Spinner className="w-auto h-auto" />
            <span className="text-[14px] text-[#6b7280]">Carregando culturas…</span>
          </div>
        ) : (
          <SelectField
            label="CULTURA"
            options={cropOptions}
            value={selectedCropId}
            onChange={setSelectedCropId}
            iconSrc="/icons/milho.svg"
          />
        )}

        {error && (
          <p className="text-[13px] text-[#c01b1b] leading-snug bg-[#ffebeb] rounded-lg px-3 py-2">
            {error}
          </p>
        )}

        <div className="h-2" />

        <button
          onClick={handleStart}
          disabled={loadingData || !selectedCropId}
          className="w-full bg-[#0e8038] text-white py-3.5 px-5 rounded-xl text-[15px] font-semibold leading-none active:opacity-90 transition-opacity text-center disabled:opacity-60"
        >
          Iniciar
        </button>

        <p className="type-label text-[#9ca3af]">
          DADOS CLIMÁTICOS — CAMPINA GRANDE
        </p>

        {loadingData ? (
          <div className="flex gap-2">
            {[0, 1, 2].map((i) => (
              <div key={i} className="flex-1 bg-white border border-[#e5e7eb] rounded-[10px] px-3 py-2.5 h-[60px] animate-pulse" />
            ))}
          </div>
        ) : (
          <div className="flex gap-2">
            <StatCard value={tempValue}   valueColor="#f59e0b" label="Temp. média" />
            <StatCard value={precipValue} valueColor="#3b82f6" label="Precip. média" />
            <StatCard value={trendValue}  valueColor={trendColor} label="Tendência/déc." />
          </div>
        )}
      </main>
    </>
  )
}

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
