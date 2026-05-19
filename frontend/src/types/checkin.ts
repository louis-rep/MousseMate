export interface CheckIn {
  id: number;
  beer_name: string;
  brewery: string | null;
  style: string | null;
  rating: number | null;
  notes: string | null;
  latitude: number | null;
  longitude: number | null;
  venue: string | null;
  city: string | null;
  created_at: string;
  updated_at: string;
}

export interface CheckInCreate {
  beer_name: string;
  brewery?: string | null;
  style?: string | null;
  rating?: number | null;
  notes?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  venue?: string | null;
  city?: string | null;
}

export interface CheckInUpdate {
  beer_name?: string | null;
  brewery?: string | null;
  style?: string | null;
  rating?: number | null;
  notes?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  venue?: string | null;
  city?: string | null;
}

export interface StatsSummary {
  weekly_count: number;
  monthly_count: number;
  top_styles: string[];
  top_breweries: string[];
  current_streak_days: number;
}
