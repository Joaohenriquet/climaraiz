'use client'

import { useState, useEffect } from 'react'
import Image from 'next/image'
import {
  ComposedChart,
  Bar,
  Line,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
} from 'recharts'
import Spinner from '@/shared/components/Spinner'
import { getClimateTrends } from '@/shared/lib/api'
import type { TrendIndicator, TrendsResponse } from '@/shared/lib/types'

type Tab = 'precip' | 'temp'

const MUNICIPALITY_ID = 2504009

interface ChartPoint {
  year: number
  value: number
  trend: number
  mean: number
}

function buildChartData(indicator: TrendIndicator): ChartPoint[] {
  if (!indicator.annual_series || indicator.mean == null) return []
  return indicator.annual_series.map((d) => ({
    year: d.year,
    value: d.value,
    trend: parseFloat(d.fitted.toFixed(3)),
    mean: indicator.mean!,
  }))
}

function formatPValue(p: number): string {
  if (p < 0.001) return '<0,001'
  return p.toFixed(4).replace('.', ',')
}

function formatSlope(slope: number, unit: 'mm' | 'degC'): string {
  const sign = slope > 0 ? '+' : ''
  if (unit === 'degC') return `${sign}${slope.toFixed(2).replace('.', ',')}°C por década`
  return `${sign}${slope.toFixed(2).replace('.', ',')} mm por década`
}

const YEAR_TICKS = [2001, 2005, 2010, 2015, 2020, 2025]

function xTickFormatter(value: number) {
  return YEAR_TICKS.includes(value) ? String(value) : ''
}

function computeDomain(values: number[], variable: 'precip' | 'temp'): {
  yDomain: [number, number]
  yTicks: number[]
} {
  if (values.length === 0) return { yDomain: [0, 1], yTicks: [0, 1] }
  const min = Math.min(...values)
  const max = Math.max(...values)
  if (variable === 'precip') {
    const top = Math.ceil(max / 200) * 200
    return { yDomain: [0, top], yTicks: [0, top / 3, (top / 3) * 2, top].map(Math.round) }
  }
  const bot = Math.floor(min - 0.5)
  const top = Math.ceil(max + 0.5)
  const mid = parseFloat(((bot + top) / 2).toFixed(1))
  return { yDomain: [bot, top], yTicks: [bot + 0.5, mid, top - 0.5] }
}

export default function ClimaPage() {
  const [tab, setTab] = useState<Tab>('precip')
  const [trends, setTrends] = useState<TrendsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getClimateTrends(MUNICIPALITY_ID)
      .then(setTrends)
      .catch(() => setError('Erro ao carregar dados climáticos.'))
      .finally(() => setLoading(false))
  }, [])

  const precipInd = trends?.indicators?.precipitation
  const tempInd = trends?.indicators?.temperature_mean

  const precipData = precipInd?.status === 'available' ? buildChartData(precipInd) : []
  const tempData = tempInd?.status === 'available' ? buildChartData(tempInd) : []

  const activeData = tab === 'precip' ? precipData : tempData
  const activeInd = tab === 'precip' ? precipInd : tempInd

  const values = activeData.map((d) => d.value)
  const { yDomain, yTicks } = computeDomain(values, tab)

  const slope = activeInd?.trend?.slope_per_decade ?? 0
  const pValue = activeInd?.significance?.p_value ?? 1
  const significant = pValue < 0.05
  const slopeText = formatSlope(slope, tab === 'temp' ? 'degC' : 'mm')
  const pText = `p-valor = ${formatPValue(pValue)}`

  const mean = activeInd?.mean ?? 0
  const meanBadge =
    tab === 'precip'
      ? `Média ${Math.round(mean)}mm`
      : `Média ${mean.toFixed(1).replace('.', ',')}°C`

  const precip = precipInd
  const temp = tempInd

  return (
    <>
      <header className="bg-[#1b4132] flex flex-col gap-1 pb-5 pt-4 px-5 shrink-0">
        <span className="text-white text-[17px] font-semibold leading-none">
          Tendências climáticas
        </span>
        <div className="bg-[rgba(255,255,255,0.10)] self-start px-2.5 py-1 rounded-full mt-0.5">
          <span className="text-[rgba(255,255,255,0.85)] text-[11px] font-medium leading-none">
            Campina Grande – PB · 2001–2025
          </span>
        </div>
      </header>

      <main className="flex-1 flex flex-col gap-3.5 bg-[#f3f4f6] px-4 py-6 overflow-y-auto">

        {loading ? (
          <div className="flex-1 flex items-center justify-center py-16">
            <div className="flex flex-col items-center gap-3">
              <Spinner />
              <span className="text-[13px] text-[#6b7280]">Carregando dados climáticos…</span>
            </div>
          </div>
        ) : error ? (
          <p className="text-[13px] text-[#c01b1b] bg-[#ffebeb] rounded-lg px-3 py-2">{error}</p>
        ) : (
          <>
            <p className="text-[#9ca3af] text-[10px] font-medium tracking-[0.5px] uppercase">
              Resumo das variáveis
            </p>

            <div className="flex gap-2 w-full">
              <SummaryCard
                iconSrc="/icons/precip-icon.svg"
                label="Precipitação"
                slope={precip?.trend?.slope_per_decade ?? 0}
                unit="mm"
                pValue={precip?.significance?.p_value ?? 1}
                bg="#f0fcf3"
                border="#dcf9e6"
                badgeBg="#f0fcf3"
                slopeColor="#16a34a"
                direction="up"
              />
              <SummaryCard
                iconSrc="/icons/temp-icon.svg"
                label="Temperatura"
                slope={temp?.trend?.slope_per_decade ?? 0}
                unit="°C"
                pValue={temp?.significance?.p_value ?? 1}
                bg="#fff9e0"
                border="#fef1ca"
                badgeBg="#fff9e0"
                slopeColor="#da8003"
                direction="up"
              />
            </div>

            <p className="text-[#9ca3af] text-[10px] font-medium tracking-[0.5px] uppercase">
              Análise histórica
            </p>

            <div className="bg-[#e5e7eb] flex gap-0.5 p-0.5 rounded-lg w-full">
              {(['precip', 'temp'] as Tab[]).map((t) => (
                <button
                  key={t}
                  onClick={() => setTab(t)}
                  className={[
                    'flex-1 py-1.5 px-2.5 rounded-md text-[11px] leading-none transition-colors',
                    tab === t
                      ? 'bg-white text-[#111827] font-semibold'
                      : 'text-[#6b7280] font-medium',
                  ].join(' ')}
                >
                  {t === 'precip' ? 'Precipitação' : 'Temperatura'}
                </button>
              ))}
            </div>

            <div className="bg-white border border-[#e5e7eb] rounded-xl p-3.5 flex flex-col gap-2.5 w-full">
              <div className="flex items-center justify-between">
                <div className="flex flex-col gap-0.5">
                  <span className="text-[#111827] text-[13px] font-semibold leading-none">
                    {tab === 'precip' ? 'Precipitação anual' : 'Temperatura média anual'}
                  </span>
                  <span className="text-[#9ca3af] text-[11px] leading-none">
                    2001–2025 · NASA/MERRA-2
                  </span>
                </div>
                <div className="bg-[#f3f4f6] px-2 py-1 rounded">
                  <span className="text-[#6b7280] text-[10px] font-medium leading-none">
                    {meanBadge}
                  </span>
                </div>
              </div>

              <div style={{ height: 140, width: '100%' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart data={activeData} margin={{ top: 4, right: 4, bottom: 16, left: 24 }}>
                    <CartesianGrid vertical={false} stroke="#f3f4f6" strokeWidth={1} />
                    <XAxis
                      dataKey="year"
                      tickLine={false}
                      axisLine={false}
                      tick={{ fontSize: 8, fill: '#9ca3af' }}
                      tickFormatter={xTickFormatter}
                      interval={0}
                    />
                    <YAxis
                      domain={yDomain}
                      ticks={yTicks}
                      tickLine={false}
                      axisLine={false}
                      tick={{ fontSize: 8, fill: '#9ca3af' }}
                      width={26}
                    />
                    <ReferenceLine
                      y={mean}
                      stroke="rgba(156,163,175,0.6)"
                      strokeWidth={1}
                      strokeDasharray="4 3"
                    />
                    {tab === 'precip' ? (
                      <Bar dataKey="value" fill="#22c55e" radius={[2, 2, 0, 0]} maxBarSize={8} />
                    ) : (
                      <Area
                        dataKey="value"
                        stroke="#f59e0b"
                        strokeWidth={2}
                        fill="#fff9e0"
                        dot={false}
                        activeDot={{ r: 3 }}
                      />
                    )}
                    <Line
                      dataKey="trend"
                      stroke="#16a34a"
                      strokeWidth={2}
                      dot={false}
                      activeDot={false}
                    />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>

              <div className="flex gap-3.5 items-center">
                <div className="flex items-center gap-1">
                  <div className="size-2 rounded-sm" style={{ backgroundColor: tab === 'precip' ? '#22c55e' : '#f59e0b' }} />
                  <span className="text-[#6b7280] text-[9px] leading-none">
                    {tab === 'precip' ? 'Barras anuais' : 'Série histórica'}
                  </span>
                </div>
                <div className="flex items-center gap-1">
                  <div className="h-0.5 w-3.5 rounded bg-[#16a34a]" />
                  <span className="text-[#6b7280] text-[9px] leading-none">Theil–Sen</span>
                </div>
                <div className="flex items-center gap-1">
                  <div className="h-px w-3.5" style={{ backgroundColor: 'rgba(156,163,175,0.6)' }} />
                  <span className="text-[#6b7280] text-[9px] leading-none">Média</span>
                </div>
              </div>
            </div>

            <p className="text-[#9ca3af] text-[10px] font-medium tracking-[0.5px] uppercase">
              O que mudou no clima?
            </p>

            <div
              className="rounded-xl p-3.5 flex flex-col gap-2.5 w-full border"
              style={{
                backgroundColor: tab === 'precip' ? '#f0fcf3' : '#fff9e0',
                borderColor: tab === 'precip' ? '#dcf9e6' : '#fef1ca',
              }}
            >
              <div className="flex items-center gap-2.5">
                <Image
                  src={tab === 'precip' ? '/icons/trend-precip.svg' : '/icons/trend-temp.svg'}
                  alt=""
                  width={20}
                  height={20}
                  className="shrink-0"
                />
                <span className="text-[#111827] text-[13px] font-semibold leading-none">
                  Tendência geral da região
                </span>
              </div>
              <p
                className="text-[12px] leading-[18px]"
                style={{ color: tab === 'precip' ? '#384051' : '#59400d' }}
              >
                {tab === 'precip'
                  ? 'A precipitação anual apresentou tendência de '
                  : 'A temperatura média anual apresentou tendência de '}
                <strong style={{ color: tab === 'precip' ? '#111827' : '#b26301' }}>
                  {slopeText} ({pText})
                </strong>
                {significant ? ', com significância estatística.' : ', sem significância estatística.'}
              </p>
            </div>

            <div className="h-2" />
          </>
        )}
      </main>
    </>
  )
}

function SummaryCard({
  iconSrc,
  label,
  slope,
  unit,
  pValue,
  bg,
  border,
  badgeBg,
  slopeColor,
  direction,
}: {
  iconSrc: string
  label: string
  slope: number
  unit: string
  pValue: number
  bg: string
  border: string
  badgeBg: string
  slopeColor: string
  direction: 'up' | 'down'
}) {
  const significant = pValue < 0.05
  const sign = slope > 0 ? '+' : ''
  const slopeFormatted =
    unit === '°C'
      ? `${sign}${slope.toFixed(2).replace('.', ',')}${unit}`
      : `${sign}${Math.round(slope)}`
  const pFormatted = `p=${pValue.toFixed(3).replace('.', ',')}`
  const dirLabel = slope > 0 ? (direction === 'up' ? '↑ Aumento' : '↓ Redução') : '↓ Redução'

  return (
    <div className="bg-white border border-[#e5e7eb] rounded-xl flex flex-col gap-1.5 items-center px-2.5 py-3 flex-1 min-w-0">
      <div className="rounded-lg p-2 flex items-center justify-center" style={{ backgroundColor: bg }}>
        <Image src={iconSrc} alt="" width={20} height={20} />
      </div>
      <span className="text-[#6b7280] text-[10px] font-medium text-center leading-none">{label}</span>
      <div className="px-1.5 py-0.5 rounded" style={{ backgroundColor: badgeBg, borderColor: border }}>
        <span className="text-[9px] font-semibold leading-none" style={{ color: slopeColor }}>
          {dirLabel}
        </span>
      </div>
      <span className="text-[#111827] text-base font-bold leading-none">{slopeFormatted}</span>
      {unit !== '°C' && (
        <span className="text-[#9ca3af] text-[9px] leading-none">mm/déc.</span>
      )}
      <div className="px-1 py-0.5 rounded" style={{ backgroundColor: badgeBg }}>
        <span className="text-[8px] font-medium leading-none" style={{ color: slopeColor }}>
          {pFormatted}
        </span>
      </div>
      <span
        className="text-[8px] font-medium text-center leading-none"
        style={{ color: significant ? slopeColor : '#6b7280' }}
      >
        {significant ? 'Significativo' : 'Não Sig.'}
      </span>
    </div>
  )
}
