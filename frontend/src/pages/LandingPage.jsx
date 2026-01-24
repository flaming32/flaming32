import { useState, useEffect, useMemo } from "react";
import { useNavigate, Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Search, Smartphone, Database, Cpu, Loader2, X, Key, CreditCard, Moon, Sun, Shield, Eye, Package, Copy, Check } from "lucide-react";
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
  const [showCheckUsesModal, setShowCheckUsesModal] = useState(false);
  const [paymentInfo, setPaymentInfo] = useState(null);
  const [accessCodeInput, setAccessCodeInput] = useState("");
  const [checkCodeInput, setCheckCodeInput] = useState("");
  const [isVerifying, setIsVerifying] = useState(false);
  const [isChecking, setIsChecking] = useState(false);
  const [usesRemaining, setUsesRemaining] = useState(0);
  const [checkedUses, setCheckedUses] = useState(null);
  const [selectedPackage, setSelectedPackage] = useState("basic");
  
  // Reseller dashboard state
  const [showResellerModal, setShowResellerModal] = useState(false);
  const [resellerCodeInput, setResellerCodeInput] = useState("");
  const [resellerDashboard, setResellerDashboard] = useState(null);
  const [isLoadingReseller, setIsLoadingReseller] = useState(false);
  const [copiedCode, setCopiedCode] = useState(null);

  const isDark = theme === 'dark';

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

  const checkUsesBalance = async () => {
    if (!checkCodeInput.trim()) return;
    setIsChecking(true);
    setCheckedUses(null);
    try {
      const response = await axios.post(`${API}/verify-code`, { code: checkCodeInput.trim() });
      if (response.data.valid) {
        setCheckedUses(response.data.uses_remaining);
      } else {
        toast.error(response.data.message);
      }
    } catch (error) {
      toast.error("Failed to check code");
    } finally {
      setIsChecking(false);
    }
  };

  const fetchResellerDashboard = async () => {
    if (!resellerCodeInput.trim()) return;
    setIsLoadingReseller(true);
    setResellerDashboard(null);
    try {
      const response = await axios.post(`${API}/reseller/dashboard`, { 
        master_code: resellerCodeInput.trim().toUpperCase() 
      });
      setResellerDashboard(response.data);
    } catch (error) {
      if (error.response?.status === 404) {
        toast.error("Invalid reseller code. Make sure you're using the master code (starts with R-)");
      } else {
        toast.error("Failed to load reseller dashboard");
      }
    } finally {
      setIsLoadingReseller(false);
    }
  };

  const copyCode = (code) => {
    navigator.clipboard.writeText(code);
    setCopiedCode(code);
    toast.success("Code copied!");
    setTimeout(() => setCopiedCode(null), 2000);
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

  return (
    <div className={`min-h-screen flex flex-col transition-colors duration-300 ${isDark ? 'bg-zinc-950 text-white' : 'bg-white text-zinc-900'}`}>
      {/* Header */}
      <header className={`w-full p-6 flex justify-between items-center ${isDark ? '' : 'border-b border-zinc-200'}`}>
        <div className="font-brand font-extrabold text-2xl tracking-tighter uppercase">Stashorra</div>
        <div className="flex items-center gap-3">
          {/* Reseller Dashboard Button */}
          <button 
            onClick={() => setShowResellerModal(true)}
            className={`p-2 border transition-colors ${isDark ? 'border-green-500/50 hover:border-green-500 text-green-500' : 'border-green-600/50 hover:border-green-600 text-green-600'}`}
            title="Reseller Dashboard"
            data-testid="reseller-dashboard-btn"
          >
            <Package className="h-4 w-4" />
          </button>
          
          {/* Check Uses Button */}
          <button 
            onClick={() => setShowCheckUsesModal(true)}
            className={`p-2 border transition-colors ${isDark ? 'border-zinc-700 hover:border-white' : 'border-zinc-300 hover:border-zinc-900'}`}
            title="Check remaining uses"
            data-testid="check-uses-btn"
          >
            <Eye className="h-4 w-4" />
          </button>
          
          {/* Theme Toggle */}
          <button 
            onClick={toggleTheme}
            className={`p-2 border transition-colors ${isDark ? 'border-zinc-700 hover:border-white' : 'border-zinc-300 hover:border-zinc-900'}`}
            data-testid="theme-toggle"
          >
            {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </button>
          
          {/* Admin Link */}
          <Link 
            to="/admin" 
            className={`p-2 border transition-colors ${isDark ? 'border-zinc-700 hover:border-white' : 'border-zinc-300 hover:border-zinc-900'}`}
            data-testid="admin-link"
          >
            <Shield className="h-4 w-4" />
          </Link>
          
          {accessCode ? (
            <div className="flex items-center gap-2 text-sm">
              <Key className="h-4 w-4 text-green-500" />
              <span className={`font-mono ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>{usesRemaining} left</span>
            </div>
          ) : (
            <Button
              variant="outline"
              onClick={() => setShowAccessCodeModal(true)}
              className={`h-10 px-4 font-mono text-xs uppercase ${isDark ? 'bg-transparent border-zinc-700 hover:border-white' : 'bg-transparent border-zinc-300 hover:border-zinc-900'}`}
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
          <div className={`w-full max-w-2xl mx-auto border p-6 md:p-8 ${isDark ? 'bg-zinc-950 border-zinc-800' : 'bg-zinc-50 border-zinc-200'}`}>
            <div className={`font-mono text-xs uppercase tracking-widest mb-6 ${isDark ? 'text-zinc-500' : 'text-zinc-500'}`}>
              Select Your Phone
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
              {/* Brand */}
              <div>
                <label className={`font-mono text-xs uppercase tracking-widest block mb-2 ${isDark ? 'text-zinc-500' : 'text-zinc-500'}`}>Brand</label>
                <Select value={selectedBrand} onValueChange={handleBrandChange}>
                  <SelectTrigger data-testid="brand-select" className={`w-full h-12 font-headings ${isDark ? 'bg-transparent border-zinc-700' : 'bg-white border-zinc-300'}`}>
                    <SelectValue placeholder="Select brand" />
                  </SelectTrigger>
                  <SelectContent className={`max-h-[400px] ${isDark ? 'bg-zinc-900 border-zinc-700' : 'bg-white border-zinc-200'}`}>
                    <div className={`p-2 border-b sticky top-0 z-10 ${isDark ? 'border-zinc-800 bg-zinc-900' : 'border-zinc-200 bg-white'}`}>
                      <div className="relative">
                        <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-500" />
                        <Input placeholder="Search brands..." value={brandSearch} onChange={(e) => setBrandSearch(e.target.value)} className={`pl-8 h-9 text-sm ${isDark ? 'bg-zinc-800 border-zinc-700' : 'bg-zinc-100 border-zinc-200'}`} onClick={(e) => e.stopPropagation()} />
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
                  <SelectTrigger data-testid="model-select" className={`w-full h-12 font-headings disabled:opacity-50 ${isDark ? 'bg-transparent border-zinc-700' : 'bg-white border-zinc-300'}`}>
                    <SelectValue placeholder={customModel || "Select model"} />
                  </SelectTrigger>
                  <SelectContent className={`max-h-[400px] ${isDark ? 'bg-zinc-900 border-zinc-700' : 'bg-white border-zinc-200'}`}>
                    <div className={`p-2 border-b sticky top-0 z-10 ${isDark ? 'border-zinc-800 bg-zinc-900' : 'border-zinc-200 bg-white'}`}>
                      <div className="relative">
                        <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-500" />
                        <Input placeholder="Search models..." value={modelSearch} onChange={(e) => setModelSearch(e.target.value)} className={`pl-8 h-9 text-sm ${isDark ? 'bg-zinc-800 border-zinc-700' : 'bg-zinc-100 border-zinc-200'}`} onClick={(e) => e.stopPropagation()} />
                      </div>
                    </div>
                    {filteredModels.map((model) => (
                      <SelectItem key={model} value={model} className="font-headings">{model}</SelectItem>
                    ))}
                    <div className={`border-t mt-2 pt-2 px-2 pb-2 ${isDark ? 'border-zinc-800' : 'border-zinc-200'}`}>
                      <div className={`text-xs mb-2 font-mono ${isDark ? 'text-zinc-500' : 'text-zinc-500'}`}>
                        {filteredModels.length === 0 ? "Model not found?" : "Can't find your model?"}
                      </div>
                      <Input placeholder="Type model name..." value={customModel} onChange={(e) => { setCustomModel(e.target.value); setSelectedModel(""); }} className={`h-10 text-sm mb-2 ${isDark ? 'bg-zinc-800 border-zinc-700' : 'bg-zinc-100 border-zinc-200'}`} onClick={(e) => e.stopPropagation()} data-testid="custom-model-input" />
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

            <Button data-testid="search-btn" onClick={handleSearch} disabled={isSearching || !selectedBrand || (!selectedModel && !customModel)} className={`w-full h-12 font-mono uppercase tracking-wider text-sm transition-all active:scale-[0.98] disabled:opacity-50 ${isDark ? 'bg-white text-black hover:bg-zinc-200' : 'bg-zinc-900 text-white hover:bg-zinc-800'}`}>
              {isSearching ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Fetching...</> : <><Search className="mr-2 h-4 w-4" />Get Estimate</>}
            </Button>
          </div>
        </motion.div>
      </main>

      {/* Features */}
      <section className="py-24 px-4">
        <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            { icon: Database, title: "Market Data", desc: "Real market prices for accurate valuations" },
            { icon: Smartphone, title: "Detailed Assessment", desc: "Comprehensive condition questions" },
            { icon: Cpu, title: "AI Estimation", desc: "AI-powered fair reseller pricing" }
          ].map((item, i) => (
            <div key={i} className={`p-8 border transition-colors ${isDark ? 'bg-zinc-900/50 border-zinc-800 hover:border-zinc-700' : 'bg-zinc-50 border-zinc-200 hover:border-zinc-300'}`}>
              <item.icon className={`h-8 w-8 mb-4 ${isDark ? 'text-white' : 'text-zinc-900'}`} strokeWidth={1.5} />
              <h3 className="font-headings font-bold text-xl mb-2">{item.title}</h3>
              <p className={`text-sm ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>{item.desc}</p>
            </div>
          ))}
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

      {/* Check Uses Modal */}
      <Dialog open={showCheckUsesModal} onOpenChange={setShowCheckUsesModal}>
        <DialogContent className={`max-w-md ${isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-zinc-200'}`}>
          <DialogHeader>
            <DialogTitle className="font-headings text-xl flex items-center gap-2">
              <Eye className="h-5 w-5" /> Check Remaining Uses
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            <p className={`text-sm ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
              Enter your access code to check how many uses you have remaining.
            </p>
            <div className="flex gap-2">
              <Input 
                placeholder="Enter access code" 
                value={checkCodeInput} 
                onChange={(e) => setCheckCodeInput(e.target.value.toUpperCase())} 
                className={`h-12 font-mono uppercase ${isDark ? 'bg-zinc-800 border-zinc-700' : 'bg-white border-zinc-300'}`}
                data-testid="check-code-input"
              />
              <Button 
                onClick={checkUsesBalance} 
                disabled={isChecking || !checkCodeInput.trim()} 
                className={`h-12 px-6 ${isDark ? 'bg-white text-black' : 'bg-zinc-900 text-white'}`}
              >
                {isChecking ? <Loader2 className="h-4 w-4 animate-spin" /> : "Check"}
              </Button>
            </div>
            
            {checkedUses !== null && (
              <div className={`p-6 text-center border ${isDark ? 'bg-zinc-800 border-zinc-700' : 'bg-zinc-100 border-zinc-200'}`}>
                <div className="font-mono text-5xl font-bold text-green-500">{checkedUses}</div>
                <div className={`text-sm mt-2 ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>uses remaining</div>
                {checkedUses > 0 && (
                  <Button 
                    onClick={() => {
                      verifyAccessCode(checkCodeInput);
                      setShowCheckUsesModal(false);
                    }}
                    className={`mt-4 h-10 px-4 font-mono text-xs uppercase ${isDark ? 'bg-white text-black' : 'bg-zinc-900 text-white'}`}
                  >
                    Use This Code
                  </Button>
                )}
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Payment Modal */}
      <Dialog open={showPaymentModal} onOpenChange={setShowPaymentModal}>
        <DialogContent className={`max-w-md ${isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-zinc-200'}`}>
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
                  <Input placeholder="Enter access code" value={accessCodeInput} onChange={(e) => setAccessCodeInput(e.target.value.toUpperCase())} className={`h-12 font-mono uppercase ${isDark ? 'bg-zinc-800 border-zinc-700' : 'bg-white border-zinc-300'}`} />
                  <Button onClick={handleAccessCodeSubmit} disabled={isVerifying || !accessCodeInput.trim()} className={`h-12 px-6 ${isDark ? 'bg-white text-black hover:bg-zinc-200' : 'bg-zinc-900 text-white hover:bg-zinc-800'}`}>
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
        <DialogContent className={`max-w-md ${isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-zinc-200'}`}>
          <DialogHeader>
            <DialogTitle className="font-headings text-xl flex items-center gap-2"><Key className="h-5 w-5" /> Enter Access Code</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            <p className={`text-sm ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>Enter your access code to unlock price estimates.</p>
            <div className="flex gap-2">
              <Input placeholder="Enter access code" value={accessCodeInput} onChange={(e) => setAccessCodeInput(e.target.value.toUpperCase())} className={`h-12 font-mono uppercase ${isDark ? 'bg-zinc-800 border-zinc-700' : 'bg-white border-zinc-300'}`} />
              <Button onClick={handleAccessCodeSubmit} disabled={isVerifying || !accessCodeInput.trim()} className={`h-12 px-6 ${isDark ? 'bg-white text-black' : 'bg-zinc-900 text-white'}`}>
                {isVerifying ? <Loader2 className="h-4 w-4 animate-spin" /> : "Verify"}
              </Button>
            </div>
            <div className={`border-t pt-4 ${isDark ? 'border-zinc-800' : 'border-zinc-200'}`}>
              <Button variant="outline" onClick={() => { setShowAccessCodeModal(false); setShowPaymentModal(true); }} className={`w-full h-12 font-mono text-sm ${isDark ? 'bg-transparent border-zinc-700 hover:border-white' : 'bg-transparent border-zinc-300 hover:border-zinc-900'}`}>
                Don't have a code? Purchase access
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Reseller Dashboard Modal */}
      <Dialog open={showResellerModal} onOpenChange={(open) => {
        setShowResellerModal(open);
        if (!open) {
          setResellerDashboard(null);
          setResellerCodeInput("");
        }
      }}>
        <DialogContent className={`max-w-2xl max-h-[90vh] overflow-hidden flex flex-col ${isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-zinc-200'}`}>
          <DialogHeader>
            <DialogTitle className="font-headings text-xl flex items-center gap-2 text-green-500">
              <Package className="h-5 w-5" /> Reseller Dashboard
            </DialogTitle>
          </DialogHeader>
          
          {!resellerDashboard ? (
            <div className="space-y-4 mt-4">
              <p className={`text-sm ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
                Enter your reseller master code (starts with <span className="font-mono font-bold">R-</span>) to view your 20 individual codes.
              </p>
              <div className="flex gap-2">
                <Input 
                  placeholder="R-XXXXXXXX" 
                  value={resellerCodeInput} 
                  onChange={(e) => setResellerCodeInput(e.target.value.toUpperCase())} 
                  className={`h-12 font-mono uppercase ${isDark ? 'bg-zinc-800 border-zinc-700' : 'bg-white border-zinc-300'}`}
                  data-testid="reseller-code-input"
                />
                <Button 
                  onClick={fetchResellerDashboard} 
                  disabled={isLoadingReseller || !resellerCodeInput.trim()} 
                  className="h-12 px-6 bg-green-600 text-white hover:bg-green-700"
                  data-testid="reseller-submit-btn"
                >
                  {isLoadingReseller ? <Loader2 className="h-4 w-4 animate-spin" /> : "View Codes"}
                </Button>
              </div>
              <div className={`p-4 border border-dashed ${isDark ? 'border-zinc-700 bg-zinc-800/50' : 'border-zinc-300 bg-zinc-50'}`}>
                <p className={`text-xs ${isDark ? 'text-zinc-500' : 'text-zinc-500'}`}>
                  <strong>Don't have a reseller code?</strong> Purchase a reseller package (₦3,000) to get a master code with 20 individual codes to distribute.
                </p>
              </div>
            </div>
          ) : (
            <div className="flex-1 overflow-hidden flex flex-col mt-4">
              {/* Dashboard Header */}
              <div className={`p-4 border mb-4 ${isDark ? 'bg-green-500/10 border-green-500/30' : 'bg-green-50 border-green-200'}`}>
                <div className="flex items-center justify-between mb-3">
                  <div className="font-mono text-lg text-green-500 font-bold">{resellerDashboard.master_code}</div>
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={() => {
                      setResellerDashboard(null);
                      setResellerCodeInput("");
                    }}
                    className={`text-xs ${isDark ? 'border-zinc-700' : 'border-zinc-300'}`}
                  >
                    Change Code
                  </Button>
                </div>
                <div className="grid grid-cols-3 gap-4 text-center">
                  <div>
                    <div className="font-headings text-2xl font-bold">{resellerDashboard.total_codes}</div>
                    <div className={`text-xs font-mono ${isDark ? 'text-zinc-500' : 'text-zinc-500'}`}>Total</div>
                  </div>
                  <div>
                    <div className="font-headings text-2xl font-bold text-green-500">{resellerDashboard.available_codes}</div>
                    <div className={`text-xs font-mono ${isDark ? 'text-zinc-500' : 'text-zinc-500'}`}>Available</div>
                  </div>
                  <div>
                    <div className="font-headings text-2xl font-bold text-red-500">{resellerDashboard.used_codes}</div>
                    <div className={`text-xs font-mono ${isDark ? 'text-zinc-500' : 'text-zinc-500'}`}>Used</div>
                  </div>
                </div>
              </div>

              {/* Codes List */}
              <div className={`text-xs font-mono uppercase tracking-widest mb-2 ${isDark ? 'text-zinc-500' : 'text-zinc-500'}`}>
                Your Codes to Distribute
              </div>
              <div className={`flex-1 overflow-y-auto border ${isDark ? 'border-zinc-800' : 'border-zinc-200'}`}>
                {resellerDashboard.codes && resellerDashboard.codes.length > 0 ? (
                  <div className={`divide-y ${isDark ? 'divide-zinc-800' : 'divide-zinc-200'}`}>
                    {resellerDashboard.codes.map((code, idx) => (
                      <div 
                        key={code.code} 
                        className={`p-3 flex items-center justify-between ${
                          code.uses_remaining === 0 
                            ? 'opacity-50' 
                            : isDark ? 'hover:bg-zinc-800/50' : 'hover:bg-zinc-50'
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <span className={`w-6 text-center font-mono text-xs ${isDark ? 'text-zinc-600' : 'text-zinc-400'}`}>
                            {idx + 1}
                          </span>
                          <span className={`font-mono font-bold ${
                            code.uses_remaining > 0 ? 'text-green-500' : isDark ? 'text-zinc-500' : 'text-zinc-400'
                          }`}>
                            {code.code}
                          </span>
                          <span className={`text-xs px-2 py-0.5 ${
                            code.uses_remaining > 0 
                              ? 'bg-green-500/20 text-green-500' 
                              : isDark ? 'bg-zinc-800 text-zinc-500' : 'bg-zinc-200 text-zinc-500'
                          }`}>
                            {code.uses_remaining > 0 ? 'Available' : 'Used'}
                          </span>
                        </div>
                        <button
                          onClick={() => copyCode(code.code)}
                          className={`p-2 transition-colors ${
                            copiedCode === code.code 
                              ? 'text-green-500' 
                              : isDark ? 'text-zinc-500 hover:text-white' : 'text-zinc-400 hover:text-zinc-900'
                          }`}
                          title="Copy code"
                        >
                          {copiedCode === code.code ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                        </button>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className={`p-8 text-center ${isDark ? 'text-zinc-500' : 'text-zinc-400'}`}>
                    No codes found
                  </div>
                )}
              </div>

              {/* Refresh Button */}
              <Button 
                variant="outline" 
                onClick={fetchResellerDashboard}
                disabled={isLoadingReseller}
                className={`mt-4 w-full h-10 ${isDark ? 'border-zinc-700 hover:border-white' : 'border-zinc-300 hover:border-zinc-900'}`}
              >
                {isLoadingReseller ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                Refresh
              </Button>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
