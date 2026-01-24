import { useState, useEffect, useMemo, createContext, useContext } from "react";
import { useNavigate, Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Search, Smartphone, Database, Cpu, Loader2, X, Key, CreditCard, Moon, Sun, Shield } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { toast } from "sonner";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function LandingPage({ setPhoneData, setScrapedPrices, accessCode, setAccessCode, theme, toggleTheme }) {
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
  
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [showAccessCodeModal, setShowAccessCodeModal] = useState(false);
  const [paymentInfo, setPaymentInfo] = useState(null);
  const [accessCodeInput, setAccessCodeInput] = useState("");
  const [isVerifying, setIsVerifying] = useState(false);
  const [usesRemaining, setUsesRemaining] = useState(0);
  const [selectedPackage, setSelectedPackage] = useState("basic");

  useEffect(() => {
    fetchPopularPhones();
    fetchPaymentInfo();
    const savedCode = localStorage.getItem('stashorra_access_code');
    if (savedCode) verifyAccessCode(savedCode, true);
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
        if (!silent) toast.success(`Access granted! ${response.data.uses_remaining} uses remaining.`);
        setShowAccessCodeModal(false);
        setShowPaymentModal(false);
        return true;
      } else {
        if (!silent) toast.error(response.data.message);
        localStorage.removeItem('stashorra_access_code');
        setAccessCode("");
        return false;
      }
    } catch (error) {
      if (!silent) toast.error("Failed to verify access code");
      return false;
    } finally {
      setIsVerifying(false);
    }
  };

  const handleAccessCodeSubmit = () => {
    if (accessCodeInput.trim()) verifyAccessCode(accessCodeInput.trim());
  };

  const filteredBrands = useMemo(() => {
    if (!brandSearch) return brands;
    return brands.filter(b => b.name.toLowerCase().includes(brandSearch.toLowerCase()));
  }, [brands, brandSearch]);

  const filteredModels = useMemo(() => {
    if (!modelSearch) return models;
    return models.filter(m => m.toLowerCase().includes(modelSearch.toLowerCase()));
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

  const handleSearch = async () => {
    const modelToUse = selectedModel || customModel;
    if (!selectedBrand || !modelToUse) {
      toast.error("Please select brand and model");
      return;
    }
    if (!accessCode) {
      setShowPaymentModal(true);
      return;
    }
    const isValid = await verifyAccessCode(accessCode, true);
    if (!isValid) {
      setShowPaymentModal(true);
      return;
    }
    setIsSearching(true);
    try {
      const response = await axios.post(`${API}/search-phone`, { brand: selectedBrand, model: modelToUse });
      setPhoneData({ brand: selectedBrand, model: modelToUse, type: phoneType });
      setScrapedPrices(response.data);
      toast.success("Prices fetched!");
      navigate("/estimate");
    } catch (error) {
      toast.error("Failed to fetch prices");
    } finally {
      setIsSearching(false);
    }
  };

  const isDark = theme === 'dark';

  return (
    <div className={`min-h-screen flex flex-col ${isDark ? 'bg-zinc-950 text-white' : 'bg-white text-zinc-900'}`}>
      {/* Header */}
      <header className={`w-full p-6 flex justify-between items-center ${isDark ? '' : 'border-b border-zinc-200'}`}>
        <div className="font-brand font-extrabold text-2xl tracking-tighter uppercase">
          Stashorra
        </div>
        <div className="flex items-center gap-4">
          {/* Theme Toggle */}
          <button 
            onClick={toggleTheme}
            className={`p-2 rounded-none border ${isDark ? 'border-zinc-700 hover:border-white' : 'border-zinc-300 hover:border-zinc-900'} transition-colors`}
            data-testid="theme-toggle"
          >
            {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </button>
          
          {/* Admin Link */}
          <Link 
            to="/admin" 
            className={`p-2 rounded-none border ${isDark ? 'border-zinc-700 hover:border-white' : 'border-zinc-300 hover:border-zinc-900'} transition-colors`}
            data-testid="admin-link"
          >
            <Shield className="h-4 w-4" />
          </Link>
          
          {accessCode ? (
            <div className="flex items-center gap-2 text-sm">
              <Key className="h-4 w-4 text-green-500" />
              <span className={`font-mono ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>{usesRemaining} uses left</span>
            </div>
          ) : (
            <Button
              variant="outline"
              onClick={() => setShowAccessCodeModal(true)}
              className={`rounded-none h-10 px-4 font-mono text-xs uppercase ${isDark ? 'bg-transparent border-zinc-700 hover:border-white' : 'bg-transparent border-zinc-300 hover:border-zinc-900'}`}
            >
              <Key className="mr-2 h-4 w-4" />
              Enter Code
            </Button>
          )}
        </div>
      </header>

      {/* Hero */}
      <main className="flex-1 flex flex-col items-center justify-center px-4 py-16">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="text-center max-w-4xl mx-auto">
          <h1 className="font-headings font-black text-5xl sm:text-6xl md:text-7xl lg:text-8xl tracking-tight leading-[0.9] uppercase mb-6">
            What Is It<br />
            <span className={isDark ? 'text-zinc-500' : 'text-zinc-400'}>Worth?</span>
          </h1>
          <p className={`text-base md:text-lg max-w-xl mx-auto mb-12 ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
            Get instant AI-powered price estimates for your used phone.
          </p>

          {/* Search Form */}
          <div className={`w-full max-w-2xl mx-auto ${isDark ? 'bg-zinc-950 border-zinc-800' : 'bg-zinc-50 border-zinc-200'} border p-6 md:p-8`}>
            <div className={`font-mono text-xs uppercase tracking-widest mb-6 ${isDark ? 'text-zinc-500' : 'text-zinc-500'}`}>
              Select Your Phone
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
              {/* Brand */}
              <div>
                <label className={`font-mono text-xs uppercase tracking-widest block mb-2 ${isDark ? 'text-zinc-500' : 'text-zinc-500'}`}>Brand</label>
                <Select value={selectedBrand} onValueChange={handleBrandChange}>
                  <SelectTrigger data-testid="brand-select" className={`w-full rounded-none h-12 font-headings ${isDark ? 'bg-transparent border-zinc-700' : 'bg-white border-zinc-300'}`}>
                    <SelectValue placeholder="Select brand" />
                  </SelectTrigger>
                  <SelectContent className={`rounded-none max-h-[400px] ${isDark ? 'bg-zinc-900 border-zinc-700' : 'bg-white border-zinc-200'}`}>
                    <div className={`p-2 border-b sticky top-0 z-10 ${isDark ? 'border-zinc-800 bg-zinc-900' : 'border-zinc-200 bg-white'}`}>
                      <div className="relative">
                        <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-500" />
                        <Input placeholder="Search brands..." value={brandSearch} onChange={(e) => setBrandSearch(e.target.value)} className={`pl-8 rounded-none h-9 text-sm ${isDark ? 'bg-zinc-800 border-zinc-700' : 'bg-zinc-100 border-zinc-200'}`} onClick={(e) => e.stopPropagation()} />
                      </div>
                    </div>
                    {filteredBrands.map((brand) => (
                      <SelectItem key={brand.name} value={brand.name} className="font-headings">{brand.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Model */}
              <div>
                <label className={`font-mono text-xs uppercase tracking-widest block mb-2 ${isDark ? 'text-zinc-500' : 'text-zinc-500'}`}>Model</label>
                <Select value={selectedModel} onValueChange={handleModelChange} disabled={!selectedBrand}>
                  <SelectTrigger data-testid="model-select" className={`w-full rounded-none h-12 font-headings disabled:opacity-50 ${isDark ? 'bg-transparent border-zinc-700' : 'bg-white border-zinc-300'}`}>
                    <SelectValue placeholder={customModel || "Select model"} />
                  </SelectTrigger>
                  <SelectContent className={`rounded-none max-h-[400px] ${isDark ? 'bg-zinc-900 border-zinc-700' : 'bg-white border-zinc-200'}`}>
                    <div className={`p-2 border-b sticky top-0 z-10 ${isDark ? 'border-zinc-800 bg-zinc-900' : 'border-zinc-200 bg-white'}`}>
                      <div className="relative">
                        <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-500" />
                        <Input placeholder="Search models..." value={modelSearch} onChange={(e) => setModelSearch(e.target.value)} className={`pl-8 rounded-none h-9 text-sm ${isDark ? 'bg-zinc-800 border-zinc-700' : 'bg-zinc-100 border-zinc-200'}`} onClick={(e) => e.stopPropagation()} />
                      </div>
                    </div>
                    {filteredModels.map((model) => (
                      <SelectItem key={model} value={model} className="font-headings">{model}</SelectItem>
                    ))}
                    <div className={`border-t mt-2 pt-2 px-2 pb-2 ${isDark ? 'border-zinc-800' : 'border-zinc-200'}`}>
                      <div className={`text-xs mb-2 font-mono ${isDark ? 'text-zinc-500' : 'text-zinc-500'}`}>
                        {filteredModels.length === 0 ? "Model not found?" : "Can't find your model?"}
                      </div>
                      <Input placeholder="Type model name..." value={customModel} onChange={(e) => { setCustomModel(e.target.value); setSelectedModel(""); }} className={`rounded-none h-10 text-sm mb-2 ${isDark ? 'bg-zinc-800 border-zinc-700' : 'bg-zinc-100 border-zinc-200'}`} onClick={(e) => e.stopPropagation()} data-testid="custom-model-input" />
                      {customModel && <div className="text-xs text-green-500 font-mono">Using: {customModel}</div>}
                    </div>
                  </SelectContent>
                </Select>
                {customModel && !selectedModel && (
                  <div className="mt-2 flex items-center gap-2">
                    <span className="font-mono text-xs text-green-500">Custom: {customModel}</span>
                    <button onClick={() => setCustomModel("")} className="text-zinc-500 hover:text-red-500"><X className="h-3 w-3" /></button>
                  </div>
                )}
              </div>
            </div>

            <Button data-testid="search-btn" onClick={handleSearch} disabled={isSearching || !selectedBrand || (!selectedModel && !customModel)} className={`w-full rounded-none h-12 font-mono uppercase tracking-wider text-sm transition-all active:scale-[0.98] disabled:opacity-50 ${isDark ? 'bg-white text-black hover:bg-zinc-200' : 'bg-zinc-900 text-white hover:bg-zinc-800'}`}>
              {isSearching ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Fetching...</> : <><Search className="mr-2 h-4 w-4" />Get Estimate</>}
            </Button>
          </div>
        </motion.div>
      </main>

      {/* Features */}
      <section className="py-24 px-4">
        <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className={`p-8 ${isDark ? 'bg-zinc-900/50 border border-zinc-800' : 'bg-zinc-50 border border-zinc-200'}`}>
            <Database className={`h-8 w-8 mb-4 ${isDark ? 'text-white' : 'text-zinc-900'}`} strokeWidth={1.5} />
            <h3 className="font-headings font-bold text-xl mb-2">Market Data</h3>
            <p className={isDark ? 'text-zinc-400 text-sm' : 'text-zinc-600 text-sm'}>Real market prices for accurate valuations</p>
          </div>
          <div className={`p-8 ${isDark ? 'bg-zinc-900/50 border border-zinc-800' : 'bg-zinc-50 border border-zinc-200'}`}>
            <Smartphone className={`h-8 w-8 mb-4 ${isDark ? 'text-white' : 'text-zinc-900'}`} strokeWidth={1.5} />
            <h3 className="font-headings font-bold text-xl mb-2">Detailed Assessment</h3>
            <p className={isDark ? 'text-zinc-400 text-sm' : 'text-zinc-600 text-sm'}>Comprehensive condition questions</p>
          </div>
          <div className={`p-8 ${isDark ? 'bg-zinc-900/50 border border-zinc-800' : 'bg-zinc-50 border border-zinc-200'}`}>
            <Cpu className={`h-8 w-8 mb-4 ${isDark ? 'text-white' : 'text-zinc-900'}`} strokeWidth={1.5} />
            <h3 className="font-headings font-bold text-xl mb-2">AI Estimation</h3>
            <p className={isDark ? 'text-zinc-400 text-sm' : 'text-zinc-600 text-sm'}>AI-powered fair reseller pricing</p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className={`py-8 px-4 ${isDark ? 'border-t border-zinc-900' : 'border-t border-zinc-200'}`}>
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row justify-between items-center gap-4">
          <div className="font-brand font-extrabold text-xl tracking-tighter uppercase">Stashorra</div>
          <div className="flex items-center gap-6">
            <Link to="/admin" className={`font-mono text-xs uppercase ${isDark ? 'text-zinc-500 hover:text-white' : 'text-zinc-500 hover:text-zinc-900'}`}>Admin</Link>
            <span className={`font-mono text-xs ${isDark ? 'text-zinc-500' : 'text-zinc-500'}`}>© 2025 Stashorra</span>
          </div>
        </div>
      </footer>

      {/* Payment Modal */}
      <Dialog open={showPaymentModal} onOpenChange={setShowPaymentModal}>
        <DialogContent className={`rounded-none max-w-md ${isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-zinc-200'}`}>
          <DialogHeader>
            <DialogTitle className="font-headings text-xl flex items-center gap-2">
              <CreditCard className="h-5 w-5" /> Payment Required
            </DialogTitle>
          </DialogHeader>
          
          {paymentInfo && (
            <div className="space-y-6 mt-4">
              {/* Package Selection */}
              <div className="space-y-3">
                <div className={`font-mono text-xs uppercase tracking-widest ${isDark ? 'text-zinc-500' : 'text-zinc-500'}`}>Select Package</div>
                <div className="grid grid-cols-2 gap-3">
                  <button onClick={() => setSelectedPackage("basic")} className={`p-4 border text-left transition-all ${selectedPackage === "basic" ? (isDark ? 'border-white bg-zinc-800' : 'border-zinc-900 bg-zinc-100') : (isDark ? 'border-zinc-700' : 'border-zinc-200')}`}>
                    <div className="font-mono text-xl font-bold">₦{paymentInfo.packages?.basic?.amount}</div>
                    <div className={`text-xs ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>{paymentInfo.packages?.basic?.description}</div>
                  </button>
                  <button onClick={() => setSelectedPackage("reseller")} className={`p-4 border text-left transition-all relative ${selectedPackage === "reseller" ? (isDark ? 'border-white bg-zinc-800' : 'border-zinc-900 bg-zinc-100') : (isDark ? 'border-zinc-700' : 'border-zinc-200')}`}>
                    <div className="absolute -top-2 -right-2 bg-green-500 text-white text-xs px-2 py-0.5 font-mono">SAVE</div>
                    <div className="font-mono text-xl font-bold">₦{paymentInfo.packages?.reseller?.amount}</div>
                    <div className={`text-xs ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>{paymentInfo.packages?.reseller?.description}</div>
                  </button>
                </div>
              </div>

              <div className={`space-y-2 p-4 border border-dashed ${isDark ? 'bg-zinc-950 border-zinc-700' : 'bg-zinc-50 border-zinc-300'}`}>
                <div className="flex justify-between font-mono text-sm"><span className={isDark ? 'text-zinc-500' : 'text-zinc-500'}>Bank:</span><span>{paymentInfo.bank_name}</span></div>
                <div className="flex justify-between font-mono text-sm"><span className={isDark ? 'text-zinc-500' : 'text-zinc-500'}>Account:</span><span className="font-bold">{paymentInfo.account_number}</span></div>
                <div className="flex justify-between font-mono text-sm"><span className={isDark ? 'text-zinc-500' : 'text-zinc-500'}>Name:</span><span>{paymentInfo.account_name}</span></div>
              </div>

              <div className={`p-4 ${isDark ? 'bg-zinc-800/50 border border-zinc-700' : 'bg-zinc-100 border border-zinc-200'}`}>
                <p className={`text-sm ${isDark ? 'text-zinc-300' : 'text-zinc-700'}`}>After payment, send receipt to:</p>
                <p className="font-mono text-sm mt-1">{paymentInfo.email}</p>
                <p className={`text-xs mt-2 ${isDark ? 'text-zinc-500' : 'text-zinc-500'}`}>You will receive your access code via email.</p>
              </div>

              <div className={`border-t pt-4 ${isDark ? 'border-zinc-800' : 'border-zinc-200'}`}>
                <div className={`font-mono text-xs uppercase tracking-widest mb-3 ${isDark ? 'text-zinc-500' : 'text-zinc-500'}`}>Already have a code?</div>
                <div className="flex gap-2">
                  <Input placeholder="Enter access code" value={accessCodeInput} onChange={(e) => setAccessCodeInput(e.target.value.toUpperCase())} className={`rounded-none h-12 font-mono uppercase ${isDark ? 'bg-zinc-800 border-zinc-700' : 'bg-white border-zinc-300'}`} />
                  <Button onClick={handleAccessCodeSubmit} disabled={isVerifying || !accessCodeInput.trim()} className={`rounded-none h-12 px-6 ${isDark ? 'bg-white text-black hover:bg-zinc-200' : 'bg-zinc-900 text-white hover:bg-zinc-800'}`}>
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
        <DialogContent className={`rounded-none max-w-md ${isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-zinc-200'}`}>
          <DialogHeader>
            <DialogTitle className="font-headings text-xl flex items-center gap-2"><Key className="h-5 w-5" /> Enter Access Code</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            <p className={isDark ? 'text-zinc-400 text-sm' : 'text-zinc-600 text-sm'}>Enter your access code to unlock price estimates.</p>
            <div className="flex gap-2">
              <Input placeholder="Enter access code" value={accessCodeInput} onChange={(e) => setAccessCodeInput(e.target.value.toUpperCase())} className={`rounded-none h-12 font-mono uppercase ${isDark ? 'bg-zinc-800 border-zinc-700' : 'bg-white border-zinc-300'}`} />
              <Button onClick={handleAccessCodeSubmit} disabled={isVerifying || !accessCodeInput.trim()} className={`rounded-none h-12 px-6 ${isDark ? 'bg-white text-black' : 'bg-zinc-900 text-white'}`}>
                {isVerifying ? <Loader2 className="h-4 w-4 animate-spin" /> : "Verify"}
              </Button>
            </div>
            <div className={`border-t pt-4 ${isDark ? 'border-zinc-800' : 'border-zinc-200'}`}>
              <Button variant="outline" onClick={() => { setShowAccessCodeModal(false); setShowPaymentModal(true); }} className={`w-full rounded-none h-12 font-mono text-sm ${isDark ? 'bg-transparent border-zinc-700 hover:border-white' : 'bg-transparent border-zinc-300 hover:border-zinc-900'}`}>
                Don't have a code? Purchase access
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
