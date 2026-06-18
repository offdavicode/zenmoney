import { apiGet } from './api';



export interface ReportFilters {
  month?: string;
  start_date?: string;
  end_date?: string;
  category_id?: number;
}

export interface EmotionReportItem {
  emotion: string;
  label: string;
  transaction_count: number;
  total_amount: number;
  average_amount: number;
  percentage: number;
  insight_eligible: boolean;
}

export interface CategoryReportItem {
  category_id: number | null;
  category_name: string;
  is_default: boolean;
  is_essential: boolean;
  transaction_count: number;
  total_amount: number;
  percentage: number;
}

export interface SummaryReport {
  transaction_count: number;
  income_count: number;
  expense_count: number;
  total_income: number;
  total_expense: number;
  balance: number;
  average_expense: number;
  essential_expense: number;
  essential_expense_percentage: number;
  non_essential_expense: number;
  non_essential_expense_percentage: number;
  uncategorized_expense: number;
}

export interface VisualReportItem {
  key: string;
  label: string;
  transaction_count: number;
  total_amount: number;
  percentage: number;
  is_aggregated: boolean;
  insight_eligible: boolean;
}

export interface VisualReportSection {
  pie_items: VisualReportItem[];
  bar_items: VisualReportItem[];
  textual_items: VisualReportItem[];
}

export interface VisualReportResponse {
  period: { month?: string; start_date?: string; end_date?: string };
  total_expense: number;
  category_distribution: VisualReportSection;
  emotion_distribution: VisualReportSection;
}

export interface SpendingTriggerItem {
  emotion: string;
  emotion_label: string;
  category_id: number | null;
  category_name: string;
  transaction_count: number;
  total_amount: number;
  average_amount: number;
  percentage: number;
}

export interface SurvivalTrigger {
  scope: 'global' | 'category';
  category_id: number | null;
  category_name: string;
  limit_amount: number;
  spent_amount: number;
  usage_percentage: number;
}

export interface SurvivalRecommendation {
  category_id: number;
  category_name: string;
  spent_amount: number;
  limit_amount: number | null;
  exceeded_amount: number;
  usage_percentage: number | null;
  suggest_block_new_transactions?: boolean;
  message: string;
}

export interface SurvivalModeReport {
  month: string;
  is_active: boolean;
  activation_percentage: number;
  activation_reason: 'no_limits' | 'below_threshold' | 'global_limit' | 'category_limit';
  trigger: SurvivalTrigger | null;
  recommendations: SurvivalRecommendation[];
  highlighted_transaction_ids: number[];
}

export interface BalancePrediction {
  month: string;
  calculated_on: string;
  days_remaining: number;
  current_income: number;
  current_expense: number;
  current_month_balance: number;
  expected_future_recurring_income: number;
  expected_future_recurring_expense: number;
  historical_daily_variable_expense_average: number;
  expected_remaining_variable_expense: number;
  predicted_end_balance: number;
  confidence_level: string;
}



function buildQuery(filters?: ReportFilters): string {
  if (!filters) return '';
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== null) params.append(key, String(value));
  });
  const q = params.toString();
  return q ? `?${q}` : '';
}



export async function getSummary(filters?: ReportFilters): Promise<SummaryReport> {
  return apiGet<SummaryReport>(`/reports/summary${buildQuery(filters)}`);
}

export async function getReportByEmotion(filters?: ReportFilters): Promise<EmotionReportItem[]> {
  return apiGet<EmotionReportItem[]>(`/reports/by-emotion${buildQuery(filters)}`);
}

export async function getReportByCategory(filters?: ReportFilters): Promise<CategoryReportItem[]> {
  return apiGet<CategoryReportItem[]>(`/reports/by-category${buildQuery(filters)}`);
}

export async function getVisualReport(filters?: ReportFilters): Promise<VisualReportResponse> {
  return apiGet<VisualReportResponse>(`/reports/visual${buildQuery(filters)}`);
}

export async function getTriggers(filters?: ReportFilters): Promise<SpendingTriggerItem[]> {
  return apiGet<SpendingTriggerItem[]>(`/reports/triggers${buildQuery(filters)}`);
}

export interface EmotionTriggerAnalysis {
  emotion: string;
  emotion_label: string;
  role: 'reference' | 'candidate' | 'not_informed';
  transaction_count: number;
  total_amount: number;
  average_amount: number;
  reference_transaction_count: number;
  reference_average_amount: number;
  difference_percentage: number | null;
  overall_average_amount: number;
  difference_from_overall_percentage: number | null;
  sufficient_data: boolean;
  is_trigger: boolean;
  reason: string;
}

export interface EmotionSpendingAnalysisResponse {
  period: { month?: string; start_date?: string; end_date?: string };
  conclusions_enabled: boolean;
  minimum_transactions: number;
  trigger_threshold_percentage: number;
  reference_emotions: string[];
  candidate_emotions: string[];
  overall_statistics: {
    transaction_count: number;
    total_amount: number;
    average_amount: number;
  };
  reference_statistics: {
    transaction_count: number;
    total_amount: number;
    average_amount: number;
  };
  emotion_analysis: EmotionTriggerAnalysis[];
  category_distribution: SpendingTriggerItem[];
  category_triggers: any[];
  details_by_emotion: any[];
}

export async function getEmotionAnalysis(filters?: ReportFilters): Promise<EmotionSpendingAnalysisResponse> {
  return apiGet<EmotionSpendingAnalysisResponse>(`/reports/emotion-spending-analysis${buildQuery(filters)}`);
}

export async function getSurvivalModeReport(filters?: ReportFilters): Promise<SurvivalModeReport> {
  return apiGet<SurvivalModeReport>(`/reports/survival-mode${buildQuery(filters)}`);
}

export async function getBalancePrediction(filters?: ReportFilters): Promise<BalancePrediction> {
  return apiGet<BalancePrediction>(`/reports/balance-prediction${buildQuery(filters)}`);
}
