import { useState, useEffect, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Search, Smartphone, Database, Cpu, Loader2, Plus, X, Key, CreditCard } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { toast } from "sonner";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function LandingPage({ setPhoneData, setScrapedPrices, accessCode, setAccessCode }) {
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
  
  // Payment & Access
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [showAccessCodeModal, setShowAccessCodeModal] = useState(false);
  const [paymentInfo, setPaymentInfo] = useState(null);
  const [accessCodeInput, setAccessCodeInput] = useState("");
  const [isVerifying, setIsVerifying] = useState(false);
  const [usesRemaining, setUsesRemaining] = useState(0);

  useEffect(() => {
    fetchPopularPhones();
    fetchPaymentInfo();
    
    // Check if user has saved access code
    const savedCode = localStorage.getItem('stashorra_access_code');
    if (savedCode) {
      verifyAccessCode(savedCode, true);
    }
  }, []);

  const fetchPopularPhones = async () => {
    try {
      const response = await axios.get(`${API}/popular-phones`);
      setBrands(response.data.brands);
    } catch (error) {
      console.error("Failed to fetch phones:", error);
    }
  };

  const fetchPaymentInfo = async () => {
    try {
      const response = await axios.get(`${API}/payment-info`);
      setPaymentInfo(response.data);
    } catch (error) {
      console.error("Failed to fetch payment info:", error);
    }
  };

  const verifyAccessCode = async (code, silent = false) => {
    setIsVerifying(true);
    try {
      const response = await axios.post(`${API}/verify-code`, { code });
      if (response.data.valid) {
        setAccessCode(code.toUpperCase());
        setUsesRemaining(response.data.uses_remaining);
        localStorage.setItem('stashorra_access_code', code.toUpperCase());
        if (!silent) {
          toast.success(`Access granted! ${response.data.uses_remaining} uses remaining.`);
        }
        setShowAccessCodeModal(false);
        setShowPaymentModal(false);
        return true;
      } else {
        if (!silent) {
          toast.error(response.data.message);
        }
        localStorage.removeItem('stashorra_access_code');
        setAccessCode("");
        return false;
      }
    } catch (error) {
      if (!silent) {
        toast.error("Failed to verify access code");
      }
      return false;
    } finally {
      setIsVerifying(false);
    }
  };

  const handleAccessCodeSubmit = () => {
    if (accessCodeInput.trim()) {
      verifyAccessCode(accessCodeInput.trim());
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
    if (model === "__add_custom__") {
      setCustomModel("");
      return;
    }
    setSelectedModel(model);
    setCustomModel("");
    setModelSearch("");
  };

  const handleSearch = async () => {
    const modelToUse = selectedModel || customModel;
    
    if (!selectedBrand || !modelToUse) {
      toast.error("Please select brand and model");
      return;
    }

    // Check if user has valid access code
    if (!accessCode) {
      setShowPaymentModal(true);
      return;
    }

    // Verify access code is still valid
    const isValid = await verifyAccessCode(accessCode, true);
    if (!isValid) {
      setShowPaymentModal(true);
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
        <div className="flex items-center gap-4">
          {accessCode ? (
            <div className="flex items-center gap-2 text-sm">
              <Key className="h-4 w-4 text-green-500" />
              <span className="font-mono text-zinc-400">{usesRemaining} uses left</span>
            </div>
          ) : (
            <Button
              variant="outline"
              onClick={() => setShowAccessCodeModal(true)}
              className="bg-transparent border-zinc-700 hover:border-white rounded-none h-10 px-4 font-mono text-xs uppercase"
              data-testid="enter-code-btn"
            >
              <Key className="mr-2 h-4 w-4" />
              Enter Code
            </Button>
          )}
        </div>
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
                {/* Brand Selection */}
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
                        <SelectItem key={brand.name} value={brand.name} className="font-headings hover:bg-zinc-800">
                          {brand.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Model Selection */}
                <div>
                  <label className="font-mono text-xs uppercase tracking-widest text-zinc-500 block mb-2">
                    Model
                  </label>
                  <Select 
                    value={selectedModel} 
                    onValueChange={handleModelChange}
                    disabled={!selectedBrand}
                  >
                    <SelectTrigger 
                      data-testid="model-select"
                      className="w-full bg-transparent border-zinc-700 hover:border-zinc-500 rounded-none h-12 font-headings disabled:opacity-50"
                    >
                      <SelectValue placeholder={customModel || "Select model"} />
                    </SelectTrigger>
                    <SelectContent className="bg-zinc-900 border-zinc-700 rounded-none max-h-[400px]">
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
                      
                      {filteredModels.map((model) => (
                        <SelectItem key={model} value={model} className="font-headings hover:bg-zinc-800">
                          {model}
                        </SelectItem>
                      ))}
                      
                      {/* Add Custom Model Option - Always visible */}
                      <div className="border-t border-zinc-800 mt-2 pt-2 px-2 pb-2">
                        <div className="text-xs text-zinc-500 mb-2 font-mono">
                          {filteredModels.length === 0 ? "Model not found?" : "Can't find your model?"}
                        </div>
                        <Input
                          placeholder="Type model name..."
                          value={customModel}
                          onChange={(e) => {
                            setCustomModel(e.target.value);
                            setSelectedModel("");
                          }}
                          className="bg-zinc-800 border-zinc-700 rounded-none h-10 text-sm mb-2"
                          onClick={(e) => e.stopPropagation()}
                          data-testid="custom-model-input"
                        />
                        {customModel && (
                          <div className="text-xs text-green-500 font-mono">
                            Using: {customModel}
                          </div>
                        )}
                      </div>
                    </SelectContent>
                  </Select>
                  
                  {customModel && !selectedModel && (
                    <div className="mt-2 flex items-center gap-2">
                      <span className="font-mono text-xs text-green-500">Custom: {customModel}</span>
                      <button onClick={() => setCustomModel("")} className="text-zinc-500 hover:text-white">
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
                className="w-full bg-white text-black hover:bg-zinc-200 rounded-none h-12 font-mono uppercase tracking-wider text-sm transition-all active:scale-[0.98] disabled:opacity-50"
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
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="feature-card">
              <Database className="h-8 w-8 mb-4 text-white" strokeWidth={1.5} />
              <h3 className="font-headings font-bold text-xl mb-2">Market Data</h3>
              <p className="text-zinc-400 text-sm">Real market prices for accurate valuations</p>
            </div>
            <div className="feature-card">
              <Smartphone className="h-8 w-8 mb-4 text-white" strokeWidth={1.5} />
              <h3 className="font-headings font-bold text-xl mb-2">Detailed Assessment</h3>
              <p className="text-zinc-400 text-sm">Comprehensive condition questions</p>
            </div>
            <div className="feature-card">
              <Cpu className="h-8 w-8 mb-4 text-white" strokeWidth={1.5} />
              <h3 className="font-headings font-bold text-xl mb-2">AI Estimation</h3>
              <p className="text-zinc-400 text-sm">AI-powered fair reseller pricing</p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-zinc-900 py-8 px-4">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row justify-between items-center gap-4">
          <div className="font-brand font-extrabold text-xl tracking-tighter uppercase">
            Stashorra
          </div>
          <p className="font-mono text-xs text-zinc-500">© 2025 Stashorra</p>
        </div>
      </footer>

      {/* Payment Modal */}
      <Dialog open={showPaymentModal} onOpenChange={setShowPaymentModal}>
        <DialogContent className="bg-zinc-900 border-zinc-800 rounded-none max-w-md">
          <DialogHeader>
            <DialogTitle className="font-headings text-xl flex items-center gap-2">
              <CreditCard className="h-5 w-5" />
              Payment Required
            </DialogTitle>
          </DialogHeader>
          
          {paymentInfo && (
            <div className="space-y-6 mt-4">
              <div className="text-center p-6 bg-zinc-950 border border-zinc-800">
                <div className="font-mono text-4xl font-bold mb-2">
                  ₦{paymentInfo.amount}
                </div>
                <div className="text-zinc-400 text-sm">
                  for {paymentInfo.uses_per_payment} price estimates
                </div>
              </div>

              <div className="space-y-3">
                <div className="font-mono text-xs uppercase tracking-widest text-zinc-500">
                  Payment Details
                </div>
                <div className="space-y-2 p-4 bg-zinc-950 border border-dashed border-zinc-700">
                  <div className="flex justify-between font-mono text-sm">
                    <span className="text-zinc-500">Bank:</span>
                    <span>{paymentInfo.bank_name}</span>
                  </div>
                  <div className="flex justify-between font-mono text-sm">
                    <span className="text-zinc-500">Account:</span>
                    <span className="font-bold">{paymentInfo.account_number}</span>
                  </div>
                  <div className="flex justify-between font-mono text-sm">
                    <span className="text-zinc-500">Name:</span>
                    <span>{paymentInfo.account_name}</span>
                  </div>
                </div>
              </div>

              <div className="p-4 bg-zinc-800/50 border border-zinc-700">
                <p className="text-sm text-zinc-300">
                  After payment, send your receipt to:
                </p>
                <p className="font-mono text-sm text-white mt-1">
                  {paymentInfo.email}
                </p>
                <p className="text-xs text-zinc-500 mt-2">
                  You will receive your access code via email.
                </p>
              </div>

              <div className="border-t border-zinc-800 pt-4">
                <div className="font-mono text-xs uppercase tracking-widest text-zinc-500 mb-3">
                  Already have a code?
                </div>
                <div className="flex gap-2">
                  <Input
                    placeholder="Enter access code"
                    value={accessCodeInput}
                    onChange={(e) => setAccessCodeInput(e.target.value.toUpperCase())}
                    className="bg-zinc-800 border-zinc-700 rounded-none h-12 font-mono uppercase"
                    data-testid="access-code-input"
                  />
                  <Button
                    onClick={handleAccessCodeSubmit}
                    disabled={isVerifying || !accessCodeInput.trim()}
                    className="bg-white text-black hover:bg-zinc-200 rounded-none h-12 px-6"
                    data-testid="verify-code-btn"
                  >
                    {isVerifying ? <Loader2 className="h-4 w-4 animate-spin" /> : "Verify"}
                  </Button>
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Access Code Modal */}
      <Dialog open={showAccessCodeModal} onOpenChange={setShowAccessCodeModal}>
        <DialogContent className="bg-zinc-900 border-zinc-800 rounded-none max-w-md">
          <DialogHeader>
            <DialogTitle className="font-headings text-xl flex items-center gap-2">
              <Key className="h-5 w-5" />
              Enter Access Code
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4 mt-4">
            <p className="text-zinc-400 text-sm">
              Enter your access code to unlock price estimates.
            </p>
            
            <div className="flex gap-2">
              <Input
                placeholder="Enter access code"
                value={accessCodeInput}
                onChange={(e) => setAccessCodeInput(e.target.value.toUpperCase())}
                className="bg-zinc-800 border-zinc-700 rounded-none h-12 font-mono uppercase"
              />
              <Button
                onClick={handleAccessCodeSubmit}
                disabled={isVerifying || !accessCodeInput.trim()}
                className="bg-white text-black hover:bg-zinc-200 rounded-none h-12 px-6"
              >
                {isVerifying ? <Loader2 className="h-4 w-4 animate-spin" /> : "Verify"}
              </Button>
            </div>

            <div className="border-t border-zinc-800 pt-4">
              <Button
                variant="outline"
                onClick={() => {
                  setShowAccessCodeModal(false);
                  setShowPaymentModal(true);
                }}
                className="w-full bg-transparent border-zinc-700 hover:border-white rounded-none h-12 font-mono text-sm"
              >
                Don't have a code? Purchase access
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
