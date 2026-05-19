export interface Entry {
  id: number;
  brewery: string;
  style: string | null;
  volume: number | null;
  datetime: string;
  bar: string | null;
  rating: number | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface EntryCreate {
  brewery: string;
  style?: string | null;
  volume?: number | null;
  datetime: string;
  bar?: string | null;
  rating?: number | null;
  notes?: string | null;
}

export interface EntryUpdate {
  brewery?: string | null;
  style?: string | null;
  volume?: number | null;
  datetime?: string | null;
  bar?: string | null;
  rating?: number | null;
  notes?: string | null;
}

export interface StatsSummary {
  weekly_count: number;
  monthly_count: number;
  top_styles: string[];
  top_breweries: string[];
  current_streak_days: number;
}
