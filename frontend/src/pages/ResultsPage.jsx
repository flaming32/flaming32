import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { RefreshCw, Share2, CheckCircle, AlertCircle, Info, Moon, Sun } from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

export default function ResultsPage({ phoneData, scrapedPrices, estimate, theme, toggleTheme }) {
  const navigate = useNavigate();
  const isDark = theme === 'dark';

  useEffect(() => {
    if (!phoneData || !estimate) {
      navigate("/");
    }
  }, [phoneData, estimate, navigate]);

  if (!phoneData || !estimate) return null;

  const formatPrice = (price) => {
    if (!price || price === 0) return "Price Unavailable";
    return `₦${Math.round(price).toLocaleString()}`;
  };

  const getConfidenceColor = (confidence) => {
    switch (confidence) {
      case "high": return "text-green-500";
      case "medium": return "text-yellow-500";
      case "low": return "text-red-500";
      default: return isDark ? "text-zinc-400" : "text-zinc-600";
    }
  };

  const getConditionLabel = (value) => {
    if (!value || value === "not_applicable") return null;
    const labels = {
      excellent: "Excellent", good: "Good", fair: "Fair", poor: "Poor",
      cracked: "Cracked", damaged: "Damaged", yes: "Yes", no: "No",
      unlocked: "Unlocked", locked: "Locked", locked_to_carrier: "Carrier Locked",
      all_working: "All Working", front_only: "Front Only", back_only: "Back Only",
      issues: "Has Issues", partial: "Partial", some_issues: "Some Issues",
      major_issues: "Major Issues", some_replaced: "Some Replaced",
      mostly_replaced: "Mostly Replaced", loose: "Loose", intact: "Intact"
    };
    return labels[value] || value;
  };

  const getConditionColor = (key, value) => {
    if (!value || value === "not_applicable") return "";
    const goodValues = ["excellent", "yes", "unlocked", "all_working", "intact"];
    const okValues = ["good", "some_replaced", "partial", "some_issues", "front_only", "back_only"];
    const badValues = ["fair", "poor", "cracked", "damaged", "no", "locked", "locked_to_carrier", "issues", "major_issues", "mostly_replaced", "loose"];
    
    if (goodValues.includes(value)) return "text-green-500";
    if (okValues.includes(value)) return "text-yellow-500";
    if (badValues.includes(value)) return "text-red-500";
    return isDark ? "text-zinc-400" : "text-zinc-600";
  };

  const handleShare = async () => {
    const text = `My ${phoneData.brand} ${phoneData.model} is worth approximately ${formatPrice(estimate.estimated_price)}! Estimated by Stashorra.`;
    if (navigator.share) {
      try { await navigator.share({ text }); } catch (err) {}
    } else {
      try {
        await navigator.clipboard.writeText(text);
        toast.success("Copied to clipboard!");
      } catch (err) {
        toast.error("Failed to copy");
      }
    }
  };

  const condition = estimate.condition || {};
  const displayConditions = Object.entries(condition).filter(([key, value]) => value && value !== "not_applicable" && value !== "");

  const formatKeyLabel = (key) => {
    const labels = {
      screen_condition: "Screen", body_condition: "Body", battery_health: "Battery",
      speakers_working: "Speakers", cameras_working: "Cameras", buttons_working: "Buttons",
      network_status: "Network", original_parts: "Original Parts", face_id_working: "Face ID",
      touch_id_working: "Touch ID", icloud_status: "iCloud", back_glass_condition: "Back Glass",
      true_tone_working: "True Tone", fingerprint_working: "Fingerprint", face_unlock_working: "Face Unlock",
      frp_status: "FRP Lock", charging_port: "Charging Port"
    };
    return labels[key] || key.replace(/_/g, " ");
  };

  return (
    <div className={`min-h-screen flex flex-col transition-colors duration-300 ${isDark ? 'bg-zinc-950 text-white' : 'bg-white text-zinc-900'}`}>
      <header className={`w-full p-6 flex justify-between items-center ${isDark ? 'border-b border-zinc-900' : 'border-b border-zinc-200'}`}>
        <button onClick={() => navigate("/")} className="font-brand font-extrabold text-2xl tracking-tighter uppercase hover:opacity-70 transition-opacity">
          Stashorra
        </button>
        <button onClick={toggleTheme} className={`p-2 border ${isDark ? 'border-zinc-700 hover:border-white' : 'border-zinc-300 hover:border-zinc-900'}`}>
          {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
        </button>
      </header>

      <main className="flex-1 flex flex-col lg:flex-row">
        {/* Left Panel */}
        <div className={`lg:w-2/5 p-8 md:p-12 border-b lg:border-b-0 lg:border-r ${isDark ? 'bg-zinc-950 border-zinc-900' : 'bg-zinc-50 border-zinc-200'}`}>
          <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.5 }}>
            <div className="text-center mb-8">
              <div className={`w-32 h-32 mx-auto mb-6 border flex items-center justify-center ${isDark ? 'border-zinc-800 bg-zinc-900/50' : 'border-zinc-200 bg-zinc-100'}`}>
                <div className="text-center">
                  <div className="font-mono text-5xl mb-2">📱</div>
                </div>
              </div>
              <h2 className="font-headings font-bold text-2xl md:text-3xl mb-2">{phoneData.brand} {phoneData.model}</h2>
            </div>

            <div className="space-y-6">
              <div className={`font-mono text-xs uppercase tracking-widest text-center ${isDark ? 'text-zinc-500' : 'text-zinc-500'}`}>Condition Report</div>
              <div className="space-y-2">
                {displayConditions.map(([key, value]) => (
                  <div key={key} className={`flex justify-between font-mono text-sm border-b border-dashed pb-2 ${isDark ? 'border-zinc-800' : 'border-zinc-200'}`}>
                    <span className={isDark ? 'text-zinc-500' : 'text-zinc-500'}>{formatKeyLabel(key)}</span>
                    <span className={getConditionColor(key, value)}>{getConditionLabel(value)}</span>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
        </div>

        {/* Right Panel - Receipt */}
        <div className="flex-1 p-6 md:p-12 flex items-center justify-center">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.2 }} className="w-full max-w-md">
            <div className={`receipt-card p-8 ${isDark ? '' : ''}`} data-testid="receipt-card">
              <div className="text-center mb-8 pt-4">
                <div className="font-brand font-extrabold text-xl tracking-tighter uppercase mb-2">Stashorra</div>
                <div className={`font-mono text-xs uppercase tracking-widest ${isDark ? 'text-zinc-500' : 'text-zinc-500'}`}>Price Estimate</div>
                <div className={`font-mono text-xs mt-1 ${isDark ? 'text-zinc-600' : 'text-zinc-400'}`}>
                  {new Date().toLocaleDateString("en-NG", { year: "numeric", month: "long", day: "numeric", hour: "2-digit", minute: "2-digit" })}
                </div>
              </div>

              <div className="divider mb-6" />

              <div className="space-y-3 mb-6">
                <div className={`font-mono text-xs uppercase tracking-widest mb-3 ${isDark ? 'text-zinc-500' : 'text-zinc-500'}`}>Market Reference</div>
                <div className="flex justify-between font-mono text-sm">
                  <span className={isDark ? 'text-zinc-400' : 'text-zinc-500'}>New Price</span>
                  <span>{formatPrice(estimate.new_price_avg)}</span>
                </div>
                <div className="flex justify-between font-mono text-sm">
                  <span className={isDark ? 'text-zinc-400' : 'text-zinc-500'}>Used Market Avg</span>
                  <span>{formatPrice(estimate.used_price_avg)}</span>
                </div>
              </div>

              <div className="divider mb-6" />

              <div className="text-center py-6">
                <div className={`font-mono text-xs uppercase tracking-widest mb-2 ${isDark ? 'text-zinc-500' : 'text-zinc-500'}`}>Your Phone's Estimated Value</div>
                <div className="price-display text-4xl md:text-5xl font-medium" data-testid="estimated-price">
                  {formatPrice(estimate.estimated_price)}
                </div>
                <div className={`flex items-center justify-center gap-2 mt-4 font-mono text-sm ${getConfidenceColor(estimate.confidence)}`}>
                  {estimate.confidence === "high" ? <CheckCircle className="h-4 w-4" /> : estimate.confidence === "medium" ? <Info className="h-4 w-4" /> : <AlertCircle className="h-4 w-4" />}
                  <span className="uppercase tracking-wider">{estimate.confidence} Confidence</span>
                </div>
              </div>

              <div className="divider mb-6" />

              <div className="mb-6">
                <div className={`font-mono text-xs uppercase tracking-widest mb-2 ${isDark ? 'text-zinc-500' : 'text-zinc-500'}`}>Analysis</div>
                <p className={`font-mono text-sm leading-relaxed ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>{estimate.reasoning}</p>
              </div>

              <div className={`text-center pt-4 pb-2 border-t border-dashed ${isDark ? 'border-zinc-800' : 'border-zinc-300'}`}>
                <div className={`font-mono text-xs ${isDark ? 'text-zinc-600' : 'text-zinc-400'}`}>Thank you for using Stashorra</div>
                <div className={`font-mono text-xs mt-1 ${isDark ? 'text-zinc-700' : 'text-zinc-400'}`}>This is an estimate. Actual prices may vary.</div>
              </div>
            </div>

            <div className="flex gap-4 mt-8">
              <Button variant="outline" onClick={() => navigate("/")} className={`flex-1 h-12 font-mono uppercase tracking-wider text-sm ${isDark ? 'bg-transparent border-zinc-700 hover:border-white' : 'bg-transparent border-zinc-300 hover:border-zinc-900'}`} data-testid="new-estimate-btn">
                <RefreshCw className="mr-2 h-4 w-4" /> New Estimate
              </Button>
              <Button onClick={handleShare} className={`flex-1 h-12 font-mono uppercase tracking-wider text-sm ${isDark ? 'bg-white text-black hover:bg-zinc-200' : 'bg-zinc-900 text-white hover:bg-zinc-800'}`} data-testid="share-btn">
                <Share2 className="mr-2 h-4 w-4" /> Share
              </Button>
            </div>
          </motion.div>
        </div>
      </main>

      <footer className={`py-6 px-4 ${isDark ? 'border-t border-zinc-900' : 'border-t border-zinc-200'}`}>
        <div className="max-w-6xl mx-auto text-center">
          <p className={`font-mono text-xs ${isDark ? 'text-zinc-600' : 'text-zinc-400'}`}>AI-powered phone valuation • Accurate market estimates</p>
        </div>
      </footer>
    </div>
  );
}
