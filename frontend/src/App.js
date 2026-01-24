import { useState } from "react";
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

  return (
    <div className="app-container">
      <div className="noise-texture" />
      
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
          <Route 
            path="/admin" 
            element={<AdminPage />} 
          />
        </Routes>
      </BrowserRouter>
      <Toaster position="bottom-right" />
    </div>
  );
}

export default App;
