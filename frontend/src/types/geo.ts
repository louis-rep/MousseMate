export type MapScope = "me" | "mates";

export interface VenueDrinker {
  username: string;
  entry_count: number;
  liters: number;
}

export interface VenueMapPoint {
  bar_id: number;
  name: string;
  latitude: number;
  longitude: number;
  address: string | null;
  postcode: string | null;
  is_closed: boolean;
  entry_count: number;
  total_liters: number;
  last_visit: string;
  drinkers: VenueDrinker[];
}

export interface VenueMapResponse {
  scope: MapScope;
  venues: VenueMapPoint[];
}

export interface ArrondissementStat {
  arrondissement: number; // 1-20
  entry_count: number;
  total_liters: number;
}

export interface ArrondissementMapResponse {
  scope: MapScope;
  arrondissements: ArrondissementStat[];
}
