import { NavLink, Route, Routes, useNavigate } from "react-router-dom";
import ProtectedRoute from "./components/ProtectedRoute";
import { useAuth } from "./hooks/useAuth";
import Beers from "./pages/Beers";
import Feed from "./pages/Feed";
import Login from "./pages/Login";
import Mates from "./pages/Mates";
import Register from "./pages/Register";
import Stats from "./pages/Stats";

function Nav() {
  const { isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login");
  }

  if (!isAuthenticated) return null;

  return (
    <nav className="bg-amber-600 shadow-md">
      <div className="max-w-4xl mx-auto px-4 py-3 flex items-center gap-6">
        <NavLink to="/" className="text-white font-bold text-xl tracking-tight hover:opacity-80 transition-opacity">
          🍺 MousseMate
        </NavLink>
        <NavLink
          to="/"
          end
          className={({ isActive }) =>
            `text-sm font-medium px-3 py-1 rounded transition-colors ${
              isActive ? "bg-white text-amber-700" : "text-amber-100 hover:text-white hover:bg-amber-500"
            }`
          }
        >
          Feed
        </NavLink>
        <NavLink
          to="/stats"
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
        <NavLink
          to="/mates"
          className={({ isActive }) =>
            `text-sm font-medium px-3 py-1 rounded transition-colors ${
              isActive ? "bg-white text-amber-700" : "text-amber-100 hover:text-white hover:bg-amber-500"
            }`
          }
        >
          Mates
        </NavLink>
        <button
          onClick={handleLogout}
          className="ml-auto text-sm font-medium px-3 py-1 rounded text-amber-100 hover:text-white hover:bg-amber-500 transition-colors"
        >
          Sign out
        </button>
      </div>
    </nav>
  );
}

export default function App() {
  return (
    <div className="min-h-screen bg-amber-50">
      <Nav />
      <main className="max-w-4xl mx-auto px-4 py-8">
        <Routes>
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Feed />
              </ProtectedRoute>
            }
          />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route
            path="/stats"
            element={
              <ProtectedRoute>
                <Stats />
              </ProtectedRoute>
            }
          />
          <Route
            path="/beers"
            element={
              <ProtectedRoute>
                <Beers />
              </ProtectedRoute>
            }
          />
          <Route
            path="/mates"
            element={
              <ProtectedRoute>
                <Mates />
              </ProtectedRoute>
            }
          />
        </Routes>
      </main>
    </div>
  );
}
