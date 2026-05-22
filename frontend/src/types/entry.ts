export interface Entry {
  id: number;
  name: string | null;
  type: string;
  volume: number;
  drink_datetime: string;
  bar: string | null;
  rating: number | null;
  notes: string | null;
  username: string | null;
  created_at: string;
  updated_at: string;
}

export interface EntryCreate {
  name?: string | null;
  type: string;
  volume: number;
  drink_datetime: string;
  bar?: string | null;
  rating?: number | null;
  notes?: string | null;
}

export interface EntryUpdate {
  name?: string | null;
  type?: string | null;
  volume?: number | null;
  drink_datetime?: string | null;
  bar?: string | null;
  rating?: number | null;
  notes?: string | null;
}

export interface Venue {
  date: string;
  bar: string | null;
  entries: Entry[];
}

export interface DailyLiters {
  date: string;
  liters: number;
}

export interface TypeDailyLiters {
  type: string;
  daily: DailyLiters[];
}

export interface TypeLiters {
  type: string;
  liters: number;
}

export interface BarTypeLiters {
  bar: string | null;
  values: TypeLiters[];
}

export interface StatsSummary {
  weekly_count: number;
  monthly_count: number;
  top_types: string[];
  top_names: string[];
  total_liters: number;
  daily_liters: TypeDailyLiters[];
  liters_by_type: BarTypeLiters[];
}
