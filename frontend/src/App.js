import { useState } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import LandingPage from "@/pages/LandingPage";
import EstimatePage from "@/pages/EstimatePage";
import ResultsPage from "@/pages/ResultsPage";

function App() {
  const [phoneData, setPhoneData] = useState(null);
  const [scrapedPrices, setScrapedPrices] = useState(null);
  const [estimate, setEstimate] = useState(null);

  return (
    <div className="app-container">
      {/* Noise texture overlay */}
      <div className="noise-texture" />
      
      <BrowserRouter>
        <Routes>
          <Route 
            path="/" 
            element={
              <LandingPage 
                setPhoneData={setPhoneData}
                setScrapedPrices={setScrapedPrices}
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
              />
            } 
          />
        </Routes>
      </BrowserRouter>
      <Toaster position="bottom-right" />
    </div>
  );
}

export default App;
