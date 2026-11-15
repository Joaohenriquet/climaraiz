'use client'

import { useState } from 'react'
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

type Tab = 'precip' | 'temp' | 'humidity'

// ─── Data ────────────────────────────────────────────────────────────────────

const PRECIP_DATA = [
  { year: 2001, value: 820  },
  { year: 2002, value: 680  },
  { year: 2003, value: 920  },
  { year: 2004, value: 850  },
  { year: 2005, value: 1050 },
  { year: 2006, value: 780  },
  { year: 2007, value: 900  },
  { year: 2008, value: 1100 },
  { year: 2009, value: 830  },
  { year: 2010, value: 1200 },
  { year: 2011, value: 920  },
  { year: 2012, value: 580  },
  { year: 2013, value: 970  },
  { year: 2014, value: 1030 },
  { year: 2015, value: 740  },
  { year: 2016, value: 880  },
  { year: 2017, value: 1140 },
  { year: 2018, value: 850  },
  { year: 2019, value: 970  },
  { year: 2020, value: 1060 },
  { year: 2021, value: 1180 },
  { year: 2022, value: 920  },
  { year: 2023, value: 1050 },
  { year: 2024, value: 1100 },
  { year: 2025, value: 1150 },
].map((d, i) => ({ ...d, trend: Math.round(834 + i * 10.12), mean: 956 }))

const TEMP_DATA = [
  { year: 2001, value: 27.6 },
  { year: 2002, value: 27.8 },
  { year: 2003, value: 27.5 },
  { year: 2004, value: 28.0 },
  { year: 2005, value: 27.9 },
  { year: 2006, value: 28.1 },
  { year: 2007, value: 27.7 },
  { year: 2008, value: 28.2 },
  { year: 2009, value: 28.3 },
  { year: 2010, value: 27.9 },
  { year: 2011, value: 28.0 },
  { year: 2012, value: 28.4 },
  { year: 2013, value: 28.1 },
  { year: 2014, value: 28.0 },
  { year: 2015, value: 28.5 },
  { year: 2016, value: 28.2 },
  { year: 2017, value: 28.3 },
  { year: 2018, value: 28.6 },
  { year: 2019, value: 28.4 },
  { year: 2020, value: 28.7 },
  { year: 2021, value: 28.5 },
  { year: 2022, value: 28.8 },
  { year: 2023, value: 28.6 },
  { year: 2024, value: 28.9 },
  { year: 2025, value: 29.0 },
].map((d, i) => ({ ...d, trend: parseFloat((27.72 + i * 0.032).toFixed(2)), mean: 28.1 }))

const HUMIDITY_DATA = [
  { year: 2001, value: 60 },
  { year: 2002, value: 61 },
  { year: 2003, value: 59 },
  { year: 2004, value: 60 },
  { year: 2005, value: 58 },
  { year: 2006, value: 59 },
  { year: 2007, value: 60 },
  { year: 2008, value: 57 },
  { year: 2009, value: 59 },
  { year: 2010, value: 61 },
  { year: 2011, value: 58 },
  { year: 2012, value: 56 },
  { year: 2013, value: 58 },
  { year: 2014, value: 57 },
  { year: 2015, value: 59 },
  { year: 2016, value: 56 },
  { year: 2017, value: 57 },
  { year: 2018, value: 58 },
  { year: 2019, value: 55 },
  { year: 2020, value: 57 },
  { year: 2021, value: 56 },
  { year: 2022, value: 55 },
  { year: 2023, value: 57 },
  { year: 2024, value: 55 },
  { year: 2025, value: 54 },
].map((d, i) => ({ ...d, trend: parseFloat((59.04 - i * 0.12).toFixed(2)), mean: 57.6 }))

// ─── Tab config ───────────────────────────────────────────────────────────────

const YEAR_TICKS = [2001, 2005, 2010, 2015, 2020, 2025]

const TAB_CONFIG = {
  precip: {
    label: 'Precipitação',
    chartTitle: 'Precipitação anual',
    source: '2001–2025 · INMET/ANA',
    meanBadge: 'Média 956mm',
    seriesLabel: 'Barras anuais',
    seriesColor: '#22c55e',
    trendColor: '#16a34a',
    meanValue: 956,
    yDomain: [0, 1200] as [number, number],
    yTicks: [0, 400, 800, 1200],
    data: PRECIP_DATA,
    icon: '/icons/trend-precip.svg',
    cardBg: '#f0fcf3',
    cardBorder: '#dcf9e6',
    bodyColor: '#384051',
    boldColor: '#111827',
    trendText: 'A precipitação anual apresentou tendência de aumento de ',
    trendBold: '+101,24 mm por década (p-valor = 0,0336)',
    trendSuffix: ', com significância estatística.',
  },
  temp: {
    label: 'Temperatura',
    chartTitle: 'Temperatura média anual',
    source: '2001–2025 · INMET/ERA5',
    meanBadge: 'Média 28,1°C',
    seriesLabel: 'Série histórica',
    seriesColor: '#f59e0b',
    trendColor: '#16a34a',
    meanValue: 28.1,
    yDomain: [26.5, 30] as [number, number],
    yTicks: [27, 28, 29],
    data: TEMP_DATA,
    icon: '/icons/trend-temp.svg',
    cardBg: '#fff9e0',
    cardBorder: '#fef1ca',
    bodyColor: '#59400d',
    boldColor: '#b26301',
    trendText: 'A temperatura média anual apresentou tendência de aquecimento de ',
    trendBold: '+0,32°C por década (p-valor = 0,0412)',
    trendSuffix: ', com significância estatística.',
  },
  humidity: {
    label: 'Umidade',
    chartTitle: 'Umidade relativa anual',
    source: '2001–2025 · INMET',
    meanBadge: 'Média 57,6%',
    seriesLabel: 'Série histórica',
    seriesColor: '#60a5fa',
    trendColor: '#16a34a',
    meanValue: 57.6,
    yDomain: [52, 64] as [number, number],
    yTicks: [54, 57, 60],
    data: HUMIDITY_DATA,
    icon: '/icons/trend-humidity.svg',
    cardBg: '#e5f1ff',
    cardBorder: '#cbe3ff',
    bodyColor: '#142e6b',
    boldColor: '#1e5ad7',
    trendText: 'A umidade relativa apresentou tendência de redução de ',
    trendBold: '-1,20% por década (p-valor = 0,0892)',
    trendSuffix: ', sem significância estatística.',
  },
} as const

// ─── Helpers ─────────────────────────────────────────────────────────────────

function xTickFormatter(value: number) {
  return YEAR_TICKS.includes(value) ? String(value) : ''
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function ClimaPage() {
  const [tab, setTab] = useState<Tab>('precip')
  const cfg = TAB_CONFIG[tab]

  const tabs: Tab[] = ['precip', 'temp', 'humidity']

  return (
    <>
      {/* Header */}
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

        {/* Section label */}
        <p className="text-[#9ca3af] text-[10px] font-medium tracking-[0.5px] uppercase">
          Resumo das variáveis
        </p>

        {/* Variable summary cards */}
        <div className="flex gap-2 w-full">
          {/* Precipitação */}
          <div className="bg-white border border-[#e5e7eb] rounded-xl flex flex-col gap-1.5 items-center px-2.5 py-3 flex-1 min-w-0">
            <div className="bg-[#f0fcf3] rounded-lg p-2 flex items-center justify-center">
              <Image src="/icons/precip-icon.svg" alt="" width={20} height={20} />
            </div>
            <span className="text-[#6b7280] text-[10px] font-medium text-center leading-none">Precipitação</span>
            <div className="bg-[#f0fcf3] px-1.5 py-0.5 rounded">
              <span className="text-[#16a34a] text-[9px] font-semibold leading-none">↑ Aumento</span>
            </div>
            <span className="text-[#111827] text-base font-bold leading-none">+101,24</span>
            <span className="text-[#9ca3af] text-[9px] leading-none">mm/déc.</span>
            <div className="bg-[#f0fcf3] px-1 py-0.5 rounded">
              <span className="text-[#16a34a] text-[8px] font-medium leading-none">p=0,034</span>
            </div>
            <span className="text-[#16a34a] text-[8px] font-medium text-center leading-none">Significativo</span>
          </div>

          {/* Temperatura */}
          <div className="bg-white border border-[#e5e7eb] rounded-xl flex flex-col gap-1.5 items-center px-2.5 py-3 flex-1 min-w-0">
            <div className="bg-[#fff9e0] rounded-lg p-2 flex items-center justify-center">
              <Image src="/icons/temp-icon.svg" alt="" width={20} height={20} />
            </div>
            <span className="text-[#6b7280] text-[10px] font-medium text-center leading-none">Temperatura</span>
            <div className="bg-[#fff9e0] px-1.5 py-0.5 rounded">
              <span className="text-[#da8003] text-[9px] font-semibold leading-none">↑ Aquecim.</span>
            </div>
            <span className="text-[#111827] text-base font-bold leading-none">+0,32</span>
            <span className="text-[#9ca3af] text-[9px] leading-none">°C/déc.</span>
            <div className="bg-[#fff9e0] px-1 py-0.5 rounded">
              <span className="text-[#da8003] text-[8px] font-medium leading-none">p=0,041</span>
            </div>
            <span className="text-[#da8003] text-[8px] font-medium text-center leading-none">Significativo</span>
          </div>

          {/* Umidade */}
          <div className="bg-white border border-[#e5e7eb] rounded-xl flex flex-col gap-1.5 items-center px-2.5 py-3 flex-1 min-w-0">
            <div className="bg-[#e5f1ff] rounded-lg p-2 flex items-center justify-center">
              <Image src="/icons/humidity-icon.svg" alt="" width={20} height={20} />
            </div>
            <span className="text-[#6b7280] text-[10px] font-medium text-center leading-none">Umidade rel.</span>
            <div className="bg-[#f3f4f6] px-1.5 py-0.5 rounded">
              <span className="text-[#6b7280] text-[9px] font-semibold leading-none">↓ Redução</span>
            </div>
            <span className="text-[#111827] text-base font-bold leading-none">-1,20</span>
            <span className="text-[#9ca3af] text-[9px] leading-none">%/déc.</span>
            <div className="bg-[#f3f4f6] px-1 py-0.5 rounded">
              <span className="text-[#6b7280] text-[8px] font-medium leading-none">p=0,089</span>
            </div>
            <span className="text-[#6b7280] text-[8px] font-medium text-center leading-none">Não Sig.</span>
          </div>
        </div>

        {/* Section label */}
        <p className="text-[#9ca3af] text-[10px] font-medium tracking-[0.5px] uppercase">
          Análise histórica
        </p>

        {/* Tab bar */}
        <div className="bg-[#e5e7eb] flex gap-0.5 p-0.5 rounded-lg w-full">
          {tabs.map((t) => (
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
              {TAB_CONFIG[t].label}
            </button>
          ))}
        </div>

        {/* Chart card */}
        <div className="bg-white border border-[#e5e7eb] rounded-xl p-3.5 flex flex-col gap-2.5 w-full">
          {/* Chart header */}
          <div className="flex items-center justify-between">
            <div className="flex flex-col gap-0.5">
              <span className="text-[#111827] text-[13px] font-semibold leading-none">
                {cfg.chartTitle}
              </span>
              <span className="text-[#9ca3af] text-[11px] leading-none">{cfg.source}</span>
            </div>
            <div className="bg-[#f3f4f6] px-2 py-1 rounded">
              <span className="text-[#6b7280] text-[10px] font-medium leading-none">
                {cfg.meanBadge}
              </span>
            </div>
          </div>

          {/* Recharts */}
          <div style={{ height: 140, width: '100%' }}>
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={cfg.data} margin={{ top: 4, right: 4, bottom: 16, left: 24 }}>
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
                  domain={cfg.yDomain}
                  ticks={cfg.yTicks}
                  tickLine={false}
                  axisLine={false}
                  tick={{ fontSize: 8, fill: '#9ca3af' }}
                  width={26}
                />
                <ReferenceLine
                  y={cfg.meanValue}
                  stroke="rgba(156,163,175,0.6)"
                  strokeWidth={1}
                  strokeDasharray="4 3"
                />

                {tab === 'precip' ? (
                  <Bar
                    dataKey="value"
                    fill={cfg.seriesColor}
                    radius={[2, 2, 0, 0]}
                    maxBarSize={8}
                  />
                ) : (
                  <Area
                    dataKey="value"
                    stroke={cfg.seriesColor}
                    strokeWidth={2}
                    fill={cfg.cardBg}
                    dot={false}
                    activeDot={{ r: 3 }}
                  />
                )}

                <Line
                  dataKey="trend"
                  stroke={cfg.trendColor}
                  strokeWidth={2}
                  dot={false}
                  activeDot={false}
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>

          {/* Legend */}
          <div className="flex gap-3.5 items-center">
            <div className="flex items-center gap-1">
              <div
                className="size-2 rounded-sm"
                style={{ backgroundColor: cfg.seriesColor }}
              />
              <span className="text-[#6b7280] text-[9px] leading-none">
                {cfg.seriesLabel}
              </span>
            </div>
            <div className="flex items-center gap-1">
              <div className="h-0.5 w-3.5 rounded" style={{ backgroundColor: cfg.trendColor }} />
              <span className="text-[#6b7280] text-[9px] leading-none">Theil–Sen</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="h-px w-3.5" style={{ backgroundColor: 'rgba(156,163,175,0.6)' }} />
              <span className="text-[#6b7280] text-[9px] leading-none">Média</span>
            </div>
          </div>
        </div>

        {/* Section label */}
        <p className="text-[#9ca3af] text-[10px] font-medium tracking-[0.5px] uppercase">
          O que mudou no clima?
        </p>

        {/* Trend description card */}
        <div
          className="rounded-xl p-3.5 flex flex-col gap-2.5 w-full border"
          style={{ backgroundColor: cfg.cardBg, borderColor: cfg.cardBorder }}
        >
          <div className="flex items-center gap-2.5">
            <Image src={cfg.icon} alt="" width={20} height={20} className="shrink-0" />
            <span className="text-[#111827] text-[13px] font-semibold leading-none">
              Tendência geral da região
            </span>
          </div>
          <p className="text-[12px] leading-[18px]" style={{ color: cfg.bodyColor }}>
            {cfg.trendText}
            <strong style={{ color: cfg.boldColor }}>{cfg.trendBold}</strong>
            {cfg.trendSuffix}
          </p>
        </div>

        <div className="h-2" />
      </main>
    </>
  )
}
