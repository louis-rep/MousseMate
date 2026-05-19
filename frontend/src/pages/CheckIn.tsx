import { useState, type FormEvent } from "react";
import { createCheckin } from "../api/checkins";
import type { CheckInCreate } from "../types/checkin";

const BEER_STYLES = [
  "IPA",
  "Stout",
  "Lager",
  "Wheat",
  "Sour",
  "Pale Ale",
  "Other",
];

interface FormState {
  beer_name: string;
  brewery: string;
  style: string;
  rating: string;
  notes: string;
}

const EMPTY_FORM: FormState = {
  beer_name: "",
  brewery: "",
  style: "",
  rating: "",
  notes: "",
};

export default function CheckIn() {
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  function handleChange(
    e: React.ChangeEvent<
      HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement
    >
  ) {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setLoading(true);

    const payload: CheckInCreate = {
      beer_name: form.beer_name.trim(),
      brewery: form.brewery.trim() || null,
      style: form.style || null,
      rating: form.rating !== "" ? parseFloat(form.rating) : null,
      notes: form.notes.trim() || null,
    };

    try {
      const created = await createCheckin(payload);
      setSuccess(`"${created.beer_name}" logged successfully!`);
      setForm(EMPTY_FORM);
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
        <div className="mb-4 p-3 rounded-lg bg-green-100 border border-green-300 text-green-800 text-sm">
          {success}
        </div>
      )}
      {error && (
        <div className="mb-4 p-3 rounded-lg bg-red-100 border border-red-300 text-red-800 text-sm">
          {error}
        </div>
      )}

      <form
        onSubmit={handleSubmit}
        className="bg-white rounded-2xl shadow-md p-6 space-y-5"
      >
        {/* Beer name */}
        <div>
          <label
            htmlFor="beer_name"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Beer Name <span className="text-red-500">*</span>
          </label>
          <input
            id="beer_name"
            name="beer_name"
            type="text"
            required
            value={form.beer_name}
            onChange={handleChange}
            placeholder="e.g. Guinness Draught"
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400"
          />
        </div>

        {/* Brewery */}
        <div>
          <label
            htmlFor="brewery"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Brewery
          </label>
          <input
            id="brewery"
            name="brewery"
            type="text"
            value={form.brewery}
            onChange={handleChange}
            placeholder="e.g. Guinness"
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400"
          />
        </div>

        {/* Style */}
        <div>
          <label
            htmlFor="style"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
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
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>

        {/* Rating */}
        <div>
          <label
            htmlFor="rating"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Rating{" "}
            <span className="text-gray-400 font-normal">(0 – 5)</span>
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

        {/* Notes */}
        <div>
          <label
            htmlFor="notes"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
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
          {loading ? "Logging…" : "Log Check-in 🍺"}
        </button>
      </form>
    </div>
  );
}
