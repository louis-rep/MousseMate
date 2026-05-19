import { useState, type FormEvent } from "react";
import { createEntry } from "../api/entries";
import type { EntryCreate } from "../types/entry";

const BEER_TYPES = ["IPA", "Stout", "Lager", "Wheat", "Sour", "Pale Ale", "Other"];

function nowLocalDatetime(): string {
  const now = new Date();
  now.setSeconds(0, 0);
  return now.toISOString().slice(0, 16);
}

interface FormState {
  name: string;
  type: string;
  volume: string;
  drink_datetime: string;
  bar: string;
  rating: string;
  notes: string;
}

function emptyForm(): FormState {
  return { name: "", type: "", volume: "", drink_datetime: nowLocalDatetime(), bar: "", rating: "", notes: "" };
}

interface Props {
  onSuccess?: () => void;
}

export default function EntryForm({ onSuccess }: Props) {
  const [form, setForm] = useState<FormState>(emptyForm);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function handleChange(e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    const payload: EntryCreate = {
      name: form.name.trim() || null,
      type: form.type,
      volume: parseFloat(form.volume),
      drink_datetime: new Date(form.drink_datetime).toISOString(),
      bar: form.bar.trim() || null,
      rating: form.rating !== "" ? parseFloat(form.rating) : null,
      notes: form.notes.trim() || null,
    };

    try {
      await createEntry(payload);
      setForm(emptyForm());
      onSuccess?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && (
        <div className="p-3 rounded-lg bg-red-100 border border-red-300 text-red-800 text-sm">{error}</div>
      )}

      <div>
        <label htmlFor="type" className="block text-sm font-medium text-gray-700 mb-1">
          Type <span className="text-red-500">*</span>
        </label>
        <select
          id="type"
          name="type"
          required
          value={form.type}
          onChange={handleChange}
          className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400 bg-white"
        >
          <option value="">— Select a type —</option>
          {BEER_TYPES.map((t) => (
            <option key={t} value={t}>{t}</option>
          ))}
        </select>
      </div>

      <div>
        <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
          Name
        </label>
        <input
          id="name"
          name="name"
          type="text"
          value={form.name}
          onChange={handleChange}
          placeholder="e.g. Guinness Draught"
          className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400"
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label htmlFor="volume" className="block text-sm font-medium text-gray-700 mb-1">
            Volume (ml) <span className="text-red-500">*</span>
          </label>
          <input
            id="volume"
            name="volume"
            type="number"
            required
            min="0"
            step="10"
            value={form.volume}
            onChange={handleChange}
            placeholder="e.g. 330"
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400"
          />
        </div>

        <div>
          <label htmlFor="rating" className="block text-sm font-medium text-gray-700 mb-1">
            Rating <span className="text-gray-400 font-normal">(0–5)</span>
          </label>
          <input
            id="rating"
            name="rating"
            type="number"
            min="0"
            max="5"
            step="0.5"
            value={form.rating}
            onChange={handleChange}
            placeholder="e.g. 4.5"
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400"
          />
        </div>
      </div>

      <div>
        <label htmlFor="drink_datetime" className="block text-sm font-medium text-gray-700 mb-1">
          Date & Time <span className="text-red-500">*</span>
        </label>
        <input
          id="drink_datetime"
          name="drink_datetime"
          type="datetime-local"
          required
          value={form.drink_datetime}
          onChange={handleChange}
          className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400"
        />
      </div>

      <div>
        <label htmlFor="bar" className="block text-sm font-medium text-gray-700 mb-1">
          Bar
        </label>
        <input
          id="bar"
          name="bar"
          type="text"
          value={form.bar}
          onChange={handleChange}
          placeholder="e.g. The Local"
          className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400"
        />
      </div>

      <div>
        <label htmlFor="notes" className="block text-sm font-medium text-gray-700 mb-1">
          Notes
        </label>
        <textarea
          id="notes"
          name="notes"
          rows={3}
          value={form.notes}
          onChange={handleChange}
          placeholder="Tasting notes, occasion, mood…"
          className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400 resize-none"
        />
      </div>

      <button
        type="submit"
        disabled={loading}
        className="w-full bg-amber-600 hover:bg-amber-700 disabled:bg-amber-300 text-white font-semibold py-2 px-4 rounded-lg transition-colors text-sm"
      >
        {loading ? "Logging…" : "Log Entry 🍺"}
      </button>
    </form>
  );
}
