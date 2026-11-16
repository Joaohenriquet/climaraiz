import axios from "axios"
import type {
  Crop,
  TrendsResponse,
  ClimateSeriesItem,
  AnalysisCreatedResponse,
  Analysis,
  AnalysisDate,
  PhasesResponse,
} from "./types"

export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  timeout: 15_000,
  headers: { "Content-Type": "application/json" },
})

export async function getCrops(): Promise<Crop[]> {
  const res = await api.get("/api/v1/crops")
  return res.data.data
}

export async function getClimateTrends(
  municipalityId: number,
  startYear = 2001,
  endYear = 2025
): Promise<TrendsResponse> {
  const res = await api.get("/api/v1/climate/trends", {
    params: { municipality_id: municipalityId, start_year: startYear, end_year: endYear },
  })
  return res.data
}

export async function getClimateSeries(
  municipalityId: number,
  variable: string,
  aggregation = "annual",
  startYear = 2001,
  endYear = 2025
): Promise<{ series: ClimateSeriesItem[]; unit: string; status: string }> {
  const res = await api.get("/api/v1/climate/series", {
    params: {
      municipality_id: municipalityId,
      variable,
      aggregation,
      start_year: startYear,
      end_year: endYear,
      limit: 1000,
    },
  })
  return res.data
}

export interface ScenarioPhase {
  id: string
  name: string
  start_day: number
  end_day: number
}

export interface PlantingRequestBody {
  municipality_id: number
  crop_id: number
  planting_year: number
  cycle_days: number
  historical_period: { start_year: number; end_year: number }
  phases: ScenarioPhase[]
  check_windows: ScenarioPhase[]
}

export async function createAnalysis(body: PlantingRequestBody): Promise<AnalysisCreatedResponse> {
  const res = await api.post("/api/v1/planting/analyses", body)
  return res.data
}

export async function getAnalysis(id: string): Promise<Analysis> {
  const res = await api.get(`/api/v1/planting/analyses/${id}`)
  return res.data
}

export async function getAnalysisDate(
  id: string,
  date: string
): Promise<AnalysisDate & { crop_id: number; analysis_id: string }> {
  const res = await api.get(`/api/v1/planting/analyses/${id}/dates/${date}`)
  return res.data
}

export async function getAnalysisDatePhases(id: string, date: string): Promise<PhasesResponse> {
  const res = await api.get(`/api/v1/planting/analyses/${id}/dates/${date}/phases`)
  return res.data
}
