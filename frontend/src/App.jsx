import { BrowserRouter, Routes, Route } from "react-router-dom";
import { DataProvider } from "./context/DataContext";
import Navbar from "./components/Navbar";
import Dashboard from "./pages/Dashboard";
import Opportunity from "./pages/Opportunity";
import Portfolio from "./pages/Portfolio";
import Simulator from "./pages/Simulator";
import Robustness from "./pages/Robustness";
import System from "./pages/System";

export default function App() {
  return (
    <DataProvider>
      <BrowserRouter>
        <Navbar />
        <main className="min-h-screen bg-bg pt-16 px-4">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/opportunity/:symbol" element={<Opportunity />} />
            <Route path="/portfolio" element={<Portfolio />} />
            <Route path="/simulator" element={<Simulator />} />
            <Route path="/robustness" element={<Robustness />} />
            <Route path="/system" element={<System />} />
          </Routes>
        </main>
      </BrowserRouter>
    </DataProvider>
  );
}
