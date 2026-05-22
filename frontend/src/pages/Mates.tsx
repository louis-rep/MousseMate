import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { followUser, listMates, searchUsers, unfollowUser } from "../api/follow";
import type { UserRead } from "../types/auth";
import type { UserSearchResult } from "../types/user";

export default function Mates() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<UserSearchResult[]>([]);
  const [mates, setMates] = useState<UserRead[]>([]);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [searching, setSearching] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    listMates().then(setMates).catch(() => null);
  }, []);

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;
    setSearching(true);
    setSearchError(null);
    searchUsers(query.trim())
      .then(setResults)
      .catch(() => setSearchError("Search failed"))
      .finally(() => setSearching(false));
  }

  async function handleFollow(userId: number) {
    await followUser(userId);
    setResults((prev) => prev.map((r) => r.id === userId ? { ...r, is_following: true } : r));
    const updated = await listMates();
    setMates(updated);
  }

  async function handleUnfollow(userId: number) {
    await unfollowUser(userId);
    setMates((prev) => prev.filter((m) => m.id !== userId));
    setResults((prev) => prev.map((r) => r.id === userId ? { ...r, is_following: false } : r));
  }

  return (
    <>
      <h1 className="text-2xl font-bold text-amber-800 mb-6">Your Mates</h1>

      {/* Search */}
      <form onSubmit={handleSearch} className="flex gap-2 mb-3">
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search by username…"
          className="flex-1 rounded-lg border border-amber-200 px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400"
        />
        <button
          type="submit"
          disabled={searching}
          className="bg-amber-600 hover:bg-amber-700 disabled:opacity-50 text-white text-sm font-semibold px-4 py-2 rounded-lg transition-colors"
        >
          Search
        </button>
      </form>

      {searchError && (
        <p className="text-red-600 text-sm mb-3">{searchError}</p>
      )}

      {results.length > 0 && (
        <div className="flex flex-col gap-2 mb-6">
          {results.map((r) => (
            <div key={r.username} className="flex items-center justify-between bg-white rounded-xl border border-amber-100 shadow-sm px-4 py-3">
              <Link to={`/profile/${r.id}`} className="text-xs font-semibold bg-amber-50 border border-amber-200 text-amber-800 px-3 py-1 rounded-full hover:bg-amber-100 transition-colors">
                {r.username}
              </Link>
              <div className="flex items-center gap-3">
                {r.is_following ? (
                  <span className="text-xs font-medium bg-amber-100 text-amber-700 px-3 py-1 rounded-full">
                    Following
                  </span>
                ) : (
                  <button
                    onClick={() => handleFollow(r.id)}
                    className="text-sm font-bold text-amber-600 hover:text-amber-800 transition-colors"
                  >
                    +
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Mates list */}
      {mates.length === 0 ? (
        <p className="text-center text-gray-400 italic py-16">No mates yet. Search for a username above.</p>
      ) : (
        <div className="flex flex-col gap-2">
          {mates.map((mate) => (
            <div key={mate.username} className="flex items-center justify-between bg-white rounded-xl border border-amber-100 shadow-sm px-4 py-3">
              <Link to={`/profile/${mate.id}`} className="text-xs font-semibold bg-amber-50 border border-amber-200 text-amber-800 px-3 py-1 rounded-full hover:bg-amber-100 transition-colors">
                {mate.username}
              </Link>
              <button
                onClick={() => handleUnfollow(mate.id)}
                className="text-xs text-gray-400 hover:text-red-500 transition-colors"
              >
                Unfollow
              </button>
            </div>
          ))}
        </div>
      )}
    </>
  );
}
