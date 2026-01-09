import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Search, Smartphone, Database, Cpu, ChevronRight, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function LandingPage({ setPhoneData, setScrapedPrices }) {
  const navigate = useNavigate();
  const [brands, setBrands] = useState([]);
  const [selectedBrand, setSelectedBrand] = useState("");
  const [selectedModel, setSelectedModel] = useState("");
  const [models, setModels] = useState([]);
  const [isSearching, setIsSearching] = useState(false);

  useEffect(() => {
    fetchPopularPhones();
  }, []);

  const fetchPopularPhones = async () => {
    try {
      const response = await axios.get(`${API}/popular-phones`);
      setBrands(response.data.brands);
    } catch (error) {
      console.error("Failed to fetch phones:", error);
    }
  };

  const handleBrandChange = (brand) => {
    setSelectedBrand(brand);
    const brandData = brands.find(b => b.name === brand);
    setModels(brandData ? brandData.models : []);
    setSelectedModel("");
  };

  const handleSearch = async () => {
    if (!selectedBrand || !selectedModel) {
      toast.error("Please select both brand and model");
      return;
    }

    setIsSearching(true);
    
    try {
      const response = await axios.post(`${API}/search-phone`, {
        brand: selectedBrand,
        model: selectedModel
      });

      setPhoneData({ brand: selectedBrand, model: selectedModel });
      setScrapedPrices(response.data);
      
      toast.success("Prices fetched successfully!");
      navigate("/estimate");
    } catch (error) {
      console.error("Search error:", error);
      toast.error("Failed to fetch prices. Please try again.");
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="w-full p-6 flex justify-between items-center">
        <div className="font-brand font-extrabold text-2xl tracking-tighter uppercase">
          Stashorra
        </div>
        <nav className="hidden md:flex gap-8">
          <a href="#features" className="font-mono text-xs uppercase tracking-widest text-zinc-400 hover:text-white transition-colors">
            Features
          </a>
          <a href="#how-it-works" className="font-mono text-xs uppercase tracking-widest text-zinc-400 hover:text-white transition-colors">
            How It Works
          </a>
        </nav>
      </header>

      {/* Hero Section */}
      <main className="flex-1 flex flex-col items-center justify-center px-4 py-16">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center max-w-4xl mx-auto"
        >
          {/* Main Headline */}
          <h1 className="font-headings font-black text-5xl sm:text-6xl md:text-7xl lg:text-8xl tracking-tight leading-[0.9] uppercase mb-6">
            What Is It
            <br />
            <span className="text-zinc-500">Worth?</span>
          </h1>

          <p className="font-body text-base md:text-lg text-zinc-400 max-w-xl mx-auto mb-12">
            Get instant AI-powered price estimates for your used phone. 
            We compare prices from Slot.ng and Jiji.ng to give you the most accurate valuation.
          </p>

          {/* Search Form */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="w-full max-w-2xl mx-auto"
          >
            <div className="bg-zinc-950 border border-zinc-800 p-6 md:p-8">
              <div className="font-mono text-xs uppercase tracking-widest text-zinc-500 mb-6">
                Select Your Phone
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                <div>
                  <label className="font-mono text-xs uppercase tracking-widest text-zinc-500 block mb-2">
                    Brand
                  </label>
                  <Select value={selectedBrand} onValueChange={handleBrandChange}>
                    <SelectTrigger 
                      data-testid="brand-select"
                      className="w-full bg-transparent border-zinc-700 hover:border-zinc-500 rounded-none h-12 font-headings"
                    >
                      <SelectValue placeholder="Select brand" />
                    </SelectTrigger>
                    <SelectContent className="bg-zinc-900 border-zinc-700 rounded-none">
                      {brands.map((brand) => (
                        <SelectItem 
                          key={brand.name} 
                          value={brand.name}
                          className="font-headings hover:bg-zinc-800"
                        >
                          {brand.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <label className="font-mono text-xs uppercase tracking-widest text-zinc-500 block mb-2">
                    Model
                  </label>
                  <Select 
                    value={selectedModel} 
                    onValueChange={setSelectedModel}
                    disabled={!selectedBrand}
                  >
                    <SelectTrigger 
                      data-testid="model-select"
                      className="w-full bg-transparent border-zinc-700 hover:border-zinc-500 rounded-none h-12 font-headings disabled:opacity-50"
                    >
                      <SelectValue placeholder="Select model" />
                    </SelectTrigger>
                    <SelectContent className="bg-zinc-900 border-zinc-700 rounded-none max-h-[300px]">
                      {models.map((model) => (
                        <SelectItem 
                          key={model} 
                          value={model}
                          className="font-headings hover:bg-zinc-800"
                        >
                          {model}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <Button
                data-testid="search-btn"
                onClick={handleSearch}
                disabled={isSearching || !selectedBrand || !selectedModel}
                className="w-full bg-white text-black hover:bg-zinc-200 rounded-none h-12 font-mono uppercase tracking-wider text-sm transition-all active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSearching ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Searching Prices...
                  </>
                ) : (
                  <>
                    <Search className="mr-2 h-4 w-4" />
                    Get Estimate
                  </>
                )}
              </Button>
            </div>
          </motion.div>
        </motion.div>
      </main>

      {/* Features Section */}
      <section id="features" className="py-24 px-4">
        <div className="max-w-6xl mx-auto">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="font-headings font-bold text-3xl md:text-4xl tracking-tight mb-4">
              How We Calculate
            </h2>
            <p className="text-zinc-400 max-w-xl mx-auto">
              Our system combines real market data with AI analysis
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.1 }}
              className="feature-card"
              data-testid="feature-scraping"
            >
              <Database className="h-8 w-8 mb-4 text-white" strokeWidth={1.5} />
              <h3 className="font-headings font-bold text-xl mb-2">Real-Time Scraping</h3>
              <p className="text-zinc-400 text-sm">
                We scan Slot.ng for brand new prices and Jiji.ng for used market rates
              </p>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.2 }}
              className="feature-card"
              data-testid="feature-condition"
            >
              <Smartphone className="h-8 w-8 mb-4 text-white" strokeWidth={1.5} />
              <h3 className="font-headings font-bold text-xl mb-2">Condition Analysis</h3>
              <p className="text-zinc-400 text-sm">
                Input your phone&apos;s screen, battery, and physical condition for accurate pricing
              </p>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.3 }}
              className="feature-card"
              data-testid="feature-ai"
            >
              <Cpu className="h-8 w-8 mb-4 text-white" strokeWidth={1.5} />
              <h3 className="font-headings font-bold text-xl mb-2">AI Estimation</h3>
              <p className="text-zinc-400 text-sm">
                Our AI analyzes all data points to give you a fair market estimate
              </p>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-zinc-900 py-8 px-4">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row justify-between items-center gap-4">
          <div className="font-brand font-extrabold text-xl tracking-tighter uppercase">
            Stashorra
          </div>
          <p className="font-mono text-xs text-zinc-500">
            © 2025 Stashorra. Fair prices for everyone.
          </p>
        </div>
      </footer>
    </div>
  );
}
