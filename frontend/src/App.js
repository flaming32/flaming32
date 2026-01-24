import { useState, useEffect } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import LandingPage from "@/pages/LandingPage";
import EstimatePage from "@/pages/EstimatePage";
import ResultsPage from "@/pages/ResultsPage";
import AdminPage from "@/pages/AdminPage";

function App() {
  const [phoneData, setPhoneData] = useState(null);
  const [scrapedPrices, setScrapedPrices] = useState(null);
  const [estimate, setEstimate] = useState(null);
  const [accessCode, setAccessCode] = useState("");
  
  // Theme state with localStorage persistence
  const [theme, setTheme] = useState(() => {
    const saved = localStorage.getItem('stashorra_theme');
    return saved || 'dark';
  });

  // Apply theme to document
  useEffect(() => {
    document.documentElement.classList.remove('light', 'dark');
    document.documentElement.classList.add(theme);
    localStorage.setItem('stashorra_theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => prev === 'dark' ? 'light' : 'dark');
  };

  return (
    <div className={`app-container ${theme}`}>
      {theme === 'dark' && <div className="noise-texture" />}
      
      <BrowserRouter>
        <Routes>
          <Route 
            path="/" 
            element={
              <LandingPage 
                setPhoneData={setPhoneData}
                setScrapedPrices={setScrapedPrices}
                accessCode={accessCode}
                setAccessCode={setAccessCode}
                theme={theme}
                toggleTheme={toggleTheme}
              />
            } 
          />
          <Route 
            path="/estimate" 
            element={
              <EstimatePage 
                phoneData={phoneData}
                scrapedPrices={scrapedPrices}
                setEstimate={setEstimate}
                accessCode={accessCode}
                theme={theme}
                toggleTheme={toggleTheme}
              />
            } 
          />
          <Route 
            path="/results" 
            element={
              <ResultsPage 
                phoneData={phoneData}
                scrapedPrices={scrapedPrices}
                estimate={estimate}
                theme={theme}
                toggleTheme={toggleTheme}
              />
            } 
          />
          <Route 
            path="/admin" 
            element={<AdminPage theme={theme} toggleTheme={toggleTheme} />} 
          />
        </Routes>
      </BrowserRouter>
      <Toaster position="bottom-right" theme={theme} />
    </div>
  );
}

export default App;
