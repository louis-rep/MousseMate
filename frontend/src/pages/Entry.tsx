import { useState, type FormEvent } from "react";
import { createEntry } from "../api/entries";
import type { EntryCreate } from "../types/entry";

const BEER_STYLES = ["IPA", "Stout", "Lager", "Wheat", "Sour", "Pale Ale", "Other"];

function nowLocalDatetime(): string {
  const now = new Date();
  now.setSeconds(0, 0);
  return now.toISOString().slice(0, 16);
}

interface FormState {
  brewery: string;
  style: string;
  volume: string;
  datetime: string;
  bar: string;
  rating: string;
  notes: string;
}

function emptyForm(): FormState {
  return { brewery: "", style: "", volume: "", datetime: nowLocalDatetime(), bar: "", rating: "", notes: "" };
}

export default function Entry() {
  const [form, setForm] = useState<FormState>(emptyForm);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  function handleChange(e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setLoading(true);

    const payload: EntryCreate = {
      brewery: form.brewery.trim(),
      style: form.style || null,
      volume: form.volume !== "" ? parseFloat(form.volume) : null,
      datetime: new Date(form.datetime).toISOString(),
      bar: form.bar.trim() || null,
      rating: form.rating !== "" ? parseFloat(form.rating) : null,
      notes: form.notes.trim() || null,
    };

    try {
      const created = await createEntry(payload);
      setSuccess(`"${created.brewery}" logged successfully!`);
      setForm(emptyForm());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-lg mx-auto">
      <h1 className="text-2xl font-bold text-amber-800 mb-6">Log a Beer</h1>

      {success && (
        <div className="mb-4 p-3 rounded-lg bg-green-100 border border-green-300 text-green-800 text-sm">{success}</div>
      )}
      {error && (
        <div className="mb-4 p-3 rounded-lg bg-red-100 border border-red-300 text-red-800 text-sm">{error}</div>
      )}

      <form onSubmit={handleSubmit} className="bg-white rounded-2xl shadow-md p-6 space-y-5">
        <div>
          <label htmlFor="brewery" className="block text-sm font-medium text-gray-700 mb-1">
            Brewery <span className="text-red-500">*</span>
          </label>
          <input
            id="brewery"
            name="brewery"
            type="text"
            required
            value={form.brewery}
            onChange={handleChange}
            placeholder="e.g. Guinness"
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400"
          />
        </div>

        <div>
          <label htmlFor="style" className="block text-sm font-medium text-gray-700 mb-1">
            Style
          </label>
          <select
            id="style"
            name="style"
            value={form.style}
            onChange={handleChange}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400 bg-white"
          >
            <option value="">— Select a style —</option>
            {BEER_STYLES.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label htmlFor="volume" className="block text-sm font-medium text-gray-700 mb-1">
              Volume <span className="text-gray-400 font-normal">(ml)</span>
            </label>
            <input
              id="volume"
              name="volume"
              type="number"
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
          <label htmlFor="datetime" className="block text-sm font-medium text-gray-700 mb-1">
            Date & Time <span className="text-red-500">*</span>
          </label>
          <input
            id="datetime"
            name="datetime"
            type="datetime-local"
            required
            value={form.datetime}
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
    </div>
  );
}
