import { useState, useEffect, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Search, Smartphone, Database, Cpu, Loader2, Plus, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { toast } from "sonner";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function LandingPage({ setPhoneData, setScrapedPrices }) {
  const navigate = useNavigate();
  const [brands, setBrands] = useState([]);
  const [selectedBrand, setSelectedBrand] = useState("");
  const [selectedModel, setSelectedModel] = useState("");
  const [customModel, setCustomModel] = useState("");
  const [models, setModels] = useState([]);
  const [phoneType, setPhoneType] = useState("android");
  const [isSearching, setIsSearching] = useState(false);
  const [brandSearch, setBrandSearch] = useState("");
  const [modelSearch, setModelSearch] = useState("");
  const [showCustomModelDialog, setShowCustomModelDialog] = useState(false);

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

  // Filter brands based on search
  const filteredBrands = useMemo(() => {
    if (!brandSearch) return brands;
    return brands.filter(b => 
      b.name.toLowerCase().includes(brandSearch.toLowerCase())
    );
  }, [brands, brandSearch]);

  // Filter models based on search
  const filteredModels = useMemo(() => {
    if (!modelSearch) return models;
    return models.filter(m => 
      m.toLowerCase().includes(modelSearch.toLowerCase())
    );
  }, [models, modelSearch]);

  const handleBrandChange = (brand) => {
    setSelectedBrand(brand);
    setBrandSearch("");
    const brandData = brands.find(b => b.name === brand);
    setModels(brandData ? brandData.models : []);
    setPhoneType(brandData?.type || "android");
    setSelectedModel("");
    setCustomModel("");
    setModelSearch("");
  };

  const handleModelChange = (model) => {
    setSelectedModel(model);
    setCustomModel("");
    setModelSearch("");
  };

  const handleCustomModelSubmit = () => {
    if (customModel.trim()) {
      setSelectedModel(customModel.trim());
      setShowCustomModelDialog(false);
    }
  };

  const handleSearch = async () => {
    const modelToUse = selectedModel || customModel;
    
    if (!selectedBrand || !modelToUse) {
      toast.error("Please select brand and model");
      return;
    }

    setIsSearching(true);
    
    try {
      const response = await axios.post(`${API}/search-phone`, {
        brand: selectedBrand,
        model: modelToUse
      });

      setPhoneData({ 
        brand: selectedBrand, 
        model: modelToUse,
        type: phoneType
      });
      setScrapedPrices(response.data);
      
      toast.success("Prices fetched!");
      navigate("/estimate");
    } catch (error) {
      console.error("Search error:", error);
      toast.error("Failed to fetch prices");
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
          <h1 className="font-headings font-black text-5xl sm:text-6xl md:text-7xl lg:text-8xl tracking-tight leading-[0.9] uppercase mb-6">
            What Is It
            <br />
            <span className="text-zinc-500">Worth?</span>
          </h1>

          <p className="font-body text-base md:text-lg text-zinc-400 max-w-xl mx-auto mb-12">
            Get instant AI-powered price estimates for your used phone. 
            Accurate valuations based on real market data and detailed condition assessment.
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
                {/* Brand Selection with Search */}
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
                    <SelectContent className="bg-zinc-900 border-zinc-700 rounded-none max-h-[400px]">
                      {/* Search Input */}
                      <div className="p-2 border-b border-zinc-800 sticky top-0 bg-zinc-900 z-10">
                        <div className="relative">
                          <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-500" />
                          <Input
                            placeholder="Search brands..."
                            value={brandSearch}
                            onChange={(e) => setBrandSearch(e.target.value)}
                            className="pl-8 bg-zinc-800 border-zinc-700 rounded-none h-9 text-sm"
                            onClick={(e) => e.stopPropagation()}
                          />
                        </div>
                      </div>
                      {filteredBrands.map((brand) => (
                        <SelectItem 
                          key={brand.name} 
                          value={brand.name}
                          className="font-headings hover:bg-zinc-800"
                        >
                          {brand.name}
                        </SelectItem>
                      ))}
                      {filteredBrands.length === 0 && (
                        <div className="p-4 text-center text-zinc-500 font-mono text-sm">
                          No brands found
                        </div>
                      )}
                    </SelectContent>
                  </Select>
                </div>

                {/* Model Selection with Search + Custom Input */}
                <div>
                  <label className="font-mono text-xs uppercase tracking-widest text-zinc-500 block mb-2">
                    Model
                  </label>
                  <div className="flex gap-2">
                    <Select 
                      value={selectedModel} 
                      onValueChange={handleModelChange}
                      disabled={!selectedBrand}
                    >
                      <SelectTrigger 
                        data-testid="model-select"
                        className="flex-1 bg-transparent border-zinc-700 hover:border-zinc-500 rounded-none h-12 font-headings disabled:opacity-50"
                      >
                        <SelectValue placeholder={customModel || "Select model"} />
                      </SelectTrigger>
                      <SelectContent className="bg-zinc-900 border-zinc-700 rounded-none max-h-[400px]">
                        {/* Search Input */}
                        <div className="p-2 border-b border-zinc-800 sticky top-0 bg-zinc-900 z-10">
                          <div className="relative">
                            <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-500" />
                            <Input
                              placeholder="Search models..."
                              value={modelSearch}
                              onChange={(e) => setModelSearch(e.target.value)}
                              className="pl-8 bg-zinc-800 border-zinc-700 rounded-none h-9 text-sm"
                              onClick={(e) => e.stopPropagation()}
                            />
                          </div>
                        </div>
                        {filteredModels.length > 0 ? (
                          filteredModels.map((model) => (
                            <SelectItem 
                              key={model} 
                              value={model}
                              className="font-headings hover:bg-zinc-800"
                            >
                              {model}
                            </SelectItem>
                          ))
                        ) : models.length === 0 ? (
                          <div className="p-4 text-center text-zinc-500 font-mono text-sm">
                            No models in database.<br/>Click + to add manually.
                          </div>
                        ) : (
                          <div className="p-4 text-center text-zinc-500 font-mono text-sm">
                            No models found
                          </div>
                        )}
                      </SelectContent>
                    </Select>
                    
                    {/* Add Custom Model Button */}
                    <Dialog open={showCustomModelDialog} onOpenChange={setShowCustomModelDialog}>
                      <DialogTrigger asChild>
                        <Button
                          variant="outline"
                          disabled={!selectedBrand}
                          className="bg-transparent border-zinc-700 hover:border-white hover:bg-zinc-800 rounded-none h-12 w-12 p-0 disabled:opacity-50"
                          data-testid="add-model-btn"
                        >
                          <Plus className="h-5 w-5" />
                        </Button>
                      </DialogTrigger>
                      <DialogContent className="bg-zinc-900 border-zinc-800 rounded-none max-w-md">
                        <DialogHeader>
                          <DialogTitle className="font-headings text-xl">
                            Add Custom Model
                          </DialogTitle>
                        </DialogHeader>
                        <div className="space-y-4 mt-4">
                          <div>
                            <label className="font-mono text-xs uppercase tracking-widest text-zinc-500 block mb-2">
                              Brand: {selectedBrand}
                            </label>
                          </div>
                          <div>
                            <label className="font-mono text-xs uppercase tracking-widest text-zinc-500 block mb-2">
                              Model Name
                            </label>
                            <Input
                              placeholder="e.g. Galaxy S25 Ultra"
                              value={customModel}
                              onChange={(e) => setCustomModel(e.target.value)}
                              className="bg-zinc-800 border-zinc-700 rounded-none h-12 font-headings"
                              data-testid="custom-model-input"
                            />
                          </div>
                          <Button
                            onClick={handleCustomModelSubmit}
                            disabled={!customModel.trim()}
                            className="w-full bg-white text-black hover:bg-zinc-200 rounded-none h-12 font-mono uppercase tracking-wider text-sm"
                            data-testid="submit-custom-model-btn"
                          >
                            Use This Model
                          </Button>
                        </div>
                      </DialogContent>
                    </Dialog>
                  </div>
                  {customModel && !selectedModel && (
                    <div className="mt-2 flex items-center gap-2">
                      <span className="font-mono text-xs text-zinc-400">Custom: {customModel}</span>
                      <button 
                        onClick={() => setCustomModel("")}
                        className="text-zinc-500 hover:text-white"
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </div>
                  )}
                </div>
              </div>

              <Button
                data-testid="search-btn"
                onClick={handleSearch}
                disabled={isSearching || !selectedBrand || (!selectedModel && !customModel)}
                className="w-full bg-white text-black hover:bg-zinc-200 rounded-none h-12 font-mono uppercase tracking-wider text-sm transition-all active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSearching ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Fetching Prices...
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
            >
              <Database className="h-8 w-8 mb-4 text-white" strokeWidth={1.5} />
              <h3 className="font-headings font-bold text-xl mb-2">Market Data</h3>
              <p className="text-zinc-400 text-sm">
                We analyze prices from multiple sources for accurate market rates
              </p>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.2 }}
              className="feature-card"
            >
              <Smartphone className="h-8 w-8 mb-4 text-white" strokeWidth={1.5} />
              <h3 className="font-headings font-bold text-xl mb-2">Detailed Assessment</h3>
              <p className="text-zinc-400 text-sm">
                Comprehensive questions for iPhone (Face ID, iCloud) and Android (FRP, charging port)
              </p>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.3 }}
              className="feature-card"
            >
              <Cpu className="h-8 w-8 mb-4 text-white" strokeWidth={1.5} />
              <h3 className="font-headings font-bold text-xl mb-2">AI Estimation</h3>
              <p className="text-zinc-400 text-sm">
                Our AI gives you a fair reseller buying price estimate
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
