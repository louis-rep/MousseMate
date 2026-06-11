export interface Bar {
  id: number;
  osm_id: number;
  osm_type: string;
  name: string;
  amenity: string;
  latitude: number;
  longitude: number;
  address: string | null;
  postcode: string | null;
  city: string;
  is_closed: boolean;
  created_at: string;
  updated_at: string;
}
