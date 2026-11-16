export interface Municipality {
  id: number
  name: string
  state: string
  latitude: number
  longitude: number
}

export interface Crop {
  id: number
  name: string
  scientific_name: string
  window_start: string
  window_end: string
  enabled: boolean
}

export interface ClimateSeriesItem {
  date: string
  value: number | null
  valid_days: number
  expected_days: number
  quality_status: 'valid' | 'incomplete'
}

export interface TrendIndicator {
  status: 'available' | 'unavailable'
  mean?: number
  minimum?: number
  maximum?: number
  minimum_year?: number
  maximum_year?: number
  unit?: string
  complete_years?: number
  trend?: {
    slope_per_decade: number
    unit: string
    confidence_interval_95?: { lower: number; upper: number }
  }
  significance?: {
    p_value: number
    tau: number
    interpretation: string
  }
  annual_series?: Array<{ year: number; value: number; fitted: number }>
}

export interface TrendsResponse {
  period: { start_year: number; end_year: number }
  indicators: {
    precipitation?: TrendIndicator
    temperature_mean?: TrendIndicator
  }
}

export interface AnalysisCreatedResponse {
  analysis_id: string
  status: string
  reused: boolean
  links: { result: string }
}

export type AnalysisStatus = 'processing' | 'completed' | 'failed'

export interface ScenarioAssessment {
  status: 'available' | 'unavailable'
  reason?: string | null
  scenario_criteria_met_pct: number | null
  evaluated_years?: number
  years_meeting_criteria?: number | null
  years_not_meeting_criteria?: number | null
  interpretation?: string
}

export interface ClimateSummary {
  mean: number
  median: number
  p10: number
  p90: number
  sample_count: number
}

export interface PhaseClimateData {
  status: string
  evaluated_years?: number
  mean_c?: ClimateSummary | null
  highest_daily_mean_c?: ClimateSummary | null
  total_mm?: ClimateSummary | null
  longest_dry_spell_days?: ClimateSummary | null
}

export interface PhaseAssessment {
  temperature_mean: PhaseClimateData
  precipitation: PhaseClimateData
  risk_level: null
  favorable_frequency_pct: null
  risk_status: string
}

export interface Phase {
  id: string
  name: string
  start_day: number
  end_day: number
  profile_status?: string
  assessment: PhaseAssessment
}

export interface PhasesResponse {
  analysis_id: string
  date: string
  status: string
  phases: Phase[]
}

export interface AnalysisDate {
  date: string
  cycle?: {
    duration_days: number
    start_day: number
    last_day: number
    estimated_last_cycle_date: string
    profile_status: string
  }
  historical_assessment: PhaseAssessment
  scenario_assessment: ScenarioAssessment
  phases_status: string
  phases?: Phase[]
}

export interface Analysis {
  analysis_id: string
  status: AnalysisStatus
  progress?: number
  error?: { code: string; message: string } | null
  municipality_id?: number
  crop_id?: number
  planting_year?: number
  window?: { start_date: string; end_date: string; source: string; version: string }
  dates?: AnalysisDate[]
}
