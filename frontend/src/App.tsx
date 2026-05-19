import { Routes, Route, NavLink } from "react-router-dom";
import Stats from "./pages/Stats";
import Beers from "./pages/Beers";

function App() {
  return (
    <div className="min-h-screen bg-amber-50">
      <nav className="bg-amber-600 shadow-md">
        <div className="max-w-4xl mx-auto px-4 py-3 flex items-center gap-6">
          <span className="text-white font-bold text-xl tracking-tight">🍺 MousseMate</span>
          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              `text-sm font-medium px-3 py-1 rounded transition-colors ${
                isActive ? "bg-white text-amber-700" : "text-amber-100 hover:text-white hover:bg-amber-500"
              }`
            }
          >
            Stats
          </NavLink>
          <NavLink
            to="/beers"
            className={({ isActive }) =>
              `text-sm font-medium px-3 py-1 rounded transition-colors ${
                isActive ? "bg-white text-amber-700" : "text-amber-100 hover:text-white hover:bg-amber-500"
              }`
            }
          >
            My Beers
          </NavLink>
        </div>
      </nav>

      <main className="max-w-4xl mx-auto px-4 py-8">
        <Routes>
          <Route path="/" element={<Stats />} />
          <Route path="/beers" element={<Beers />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
