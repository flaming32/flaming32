import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowLeft, RefreshCw, Share2, CheckCircle, AlertCircle, Info } from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

export default function ResultsPage({ phoneData, scrapedPrices, estimate }) {
  const navigate = useNavigate();

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
      default: return "text-zinc-400";
    }
  };

  const getConditionLabel = (value) => {
    return value ? value.charAt(0).toUpperCase() + value.slice(1) : "N/A";
  };

  const handleShare = async () => {
    const text = `My ${phoneData.brand} ${phoneData.model} is worth approximately ${formatPrice(estimate.estimated_price)}! Estimated by Stashorra.`;
    
    if (navigator.share) {
      try {
        await navigator.share({ text });
      } catch (err) {
        console.log("Share cancelled");
      }
    } else {
      navigator.clipboard.writeText(text);
      toast.success("Copied to clipboard!");
    }
  };

  const handleNewEstimate = () => {
    navigate("/");
  };

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="w-full p-6 flex justify-between items-center border-b border-zinc-900">
        <button 
          onClick={() => navigate("/")}
          className="font-brand font-extrabold text-2xl tracking-tighter uppercase hover:text-zinc-400 transition-colors"
          data-testid="logo-link"
        >
          Stashorra
        </button>
      </header>

      <main className="flex-1 flex flex-col lg:flex-row">
        {/* Left Panel - Phone Visual */}
        <div className="lg:w-2/5 bg-zinc-950 p-8 md:p-12 flex flex-col items-center justify-center border-b lg:border-b-0 lg:border-r border-zinc-900">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5 }}
            className="text-center"
          >
            {/* Phone Icon/Image */}
            <div className="w-48 h-48 mx-auto mb-8 border border-zinc-800 flex items-center justify-center bg-zinc-900/50">
              <div className="text-center">
                <div className="font-mono text-6xl mb-2">📱</div>
                <div className="font-mono text-xs text-zinc-500 uppercase tracking-widest">
                  {phoneData.brand}
                </div>
              </div>
            </div>

            <h2 className="font-headings font-bold text-2xl md:text-3xl mb-2">
              {phoneData.brand} {phoneData.model}
            </h2>

            {/* Condition Summary */}
            <div className="mt-8 space-y-2 text-left max-w-xs mx-auto">
              <div className="font-mono text-xs uppercase tracking-widest text-zinc-500 mb-4 text-center">
                Condition Report
              </div>
              <div className="flex justify-between font-mono text-sm border-b border-dashed border-zinc-800 pb-2">
                <span className="text-zinc-500">Screen</span>
                <span className={`${
                  estimate.condition.screen_condition === "excellent" ? "text-green-500" :
                  estimate.condition.screen_condition === "good" ? "text-green-400" :
                  estimate.condition.screen_condition === "fair" ? "text-yellow-500" : "text-red-500"
                }`}>
                  {getConditionLabel(estimate.condition.screen_condition)}
                </span>
              </div>
              <div className="flex justify-between font-mono text-sm border-b border-dashed border-zinc-800 pb-2">
                <span className="text-zinc-500">Battery</span>
                <span className={`${
                  estimate.condition.battery_health === "excellent" ? "text-green-500" :
                  estimate.condition.battery_health === "good" ? "text-green-400" :
                  estimate.condition.battery_health === "fair" ? "text-yellow-500" : "text-red-500"
                }`}>
                  {getConditionLabel(estimate.condition.battery_health)}
                </span>
              </div>
              <div className="flex justify-between font-mono text-sm">
                <span className="text-zinc-500">Damage</span>
                <span className={`${
                  estimate.condition.physical_damage === "none" ? "text-green-500" :
                  estimate.condition.physical_damage === "minor" ? "text-green-400" :
                  estimate.condition.physical_damage === "moderate" ? "text-yellow-500" : "text-red-500"
                }`}>
                  {getConditionLabel(estimate.condition.physical_damage)}
                </span>
              </div>
            </div>
          </motion.div>
        </div>

        {/* Right Panel - Receipt */}
        <div className="flex-1 p-6 md:p-12 flex items-center justify-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="w-full max-w-md"
          >
            {/* Receipt Card */}
            <div className="receipt-card p-8" data-testid="receipt-card">
              {/* Receipt Header */}
              <div className="text-center mb-8 pt-4">
                <div className="font-brand font-extrabold text-xl tracking-tighter uppercase mb-2">
                  Stashorra
                </div>
                <div className="font-mono text-xs text-zinc-500 uppercase tracking-widest">
                  Price Estimate Receipt
                </div>
                <div className="font-mono text-xs text-zinc-600 mt-1">
                  {new Date().toLocaleDateString("en-NG", {
                    year: "numeric",
                    month: "long",
                    day: "numeric",
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </div>
              </div>

              <div className="divider mb-6" />

              {/* Item Details */}
              <div className="space-y-3 mb-6">
                <div className="flex justify-between font-mono text-sm">
                  <span className="text-zinc-500">ITEM</span>
                  <span>{phoneData.brand} {phoneData.model}</span>
                </div>
              </div>

              <div className="divider mb-6" />

              {/* Price Breakdown */}
              <div className="space-y-3 mb-6">
                <div className="font-mono text-xs text-zinc-500 uppercase tracking-widest mb-3">
                  Market Reference
                </div>
                <div className="flex justify-between font-mono text-sm">
                  <span className="text-zinc-400">Slot.ng (New)</span>
                  <span>{formatPrice(estimate.new_price_avg)}</span>
                </div>
                <div className="flex justify-between font-mono text-sm">
                  <span className="text-zinc-400">Jiji.ng (Used Avg)</span>
                  <span>{formatPrice(estimate.used_price_avg)}</span>
                </div>
              </div>

              <div className="divider mb-6" />

              {/* Final Estimate */}
              <div className="text-center py-6">
                <div className="font-mono text-xs text-zinc-500 uppercase tracking-widest mb-2">
                  Estimated Value
                </div>
                <div 
                  className="price-display text-4xl md:text-5xl font-medium"
                  data-testid="estimated-price"
                >
                  {formatPrice(estimate.estimated_price)}
                </div>
                
                {/* Confidence */}
                <div className={`flex items-center justify-center gap-2 mt-4 font-mono text-sm ${getConfidenceColor(estimate.confidence)}`}>
                  {estimate.confidence === "high" ? (
                    <CheckCircle className="h-4 w-4" />
                  ) : estimate.confidence === "medium" ? (
                    <Info className="h-4 w-4" />
                  ) : (
                    <AlertCircle className="h-4 w-4" />
                  )}
                  <span className="uppercase tracking-wider">
                    {estimate.confidence} Confidence
                  </span>
                </div>
              </div>

              <div className="divider mb-6" />

              {/* AI Reasoning */}
              <div className="mb-6">
                <div className="font-mono text-xs text-zinc-500 uppercase tracking-widest mb-2">
                  Analysis
                </div>
                <p className="font-mono text-sm text-zinc-400 leading-relaxed">
                  {estimate.reasoning}
                </p>
              </div>

              {/* Receipt Footer */}
              <div className="text-center pt-4 pb-2 border-t border-dashed border-zinc-800">
                <div className="font-mono text-xs text-zinc-600">
                  Thank you for using Stashorra
                </div>
                <div className="font-mono text-xs text-zinc-700 mt-1">
                  This is an estimate only. Actual prices may vary.
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-4 mt-8">
              <Button
                variant="outline"
                onClick={handleNewEstimate}
                className="flex-1 bg-transparent border-zinc-700 hover:border-white hover:bg-transparent rounded-none h-12 font-mono uppercase tracking-wider text-sm"
                data-testid="new-estimate-btn"
              >
                <RefreshCw className="mr-2 h-4 w-4" />
                New Estimate
              </Button>
              <Button
                onClick={handleShare}
                className="flex-1 bg-white text-black hover:bg-zinc-200 rounded-none h-12 font-mono uppercase tracking-wider text-sm"
                data-testid="share-btn"
              >
                <Share2 className="mr-2 h-4 w-4" />
                Share
              </Button>
            </div>
          </motion.div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-zinc-900 py-6 px-4">
        <div className="max-w-6xl mx-auto text-center">
          <p className="font-mono text-xs text-zinc-600">
            Prices scraped from slot.ng and jiji.ng • AI-powered estimation
          </p>
        </div>
      </footer>
    </div>
  );
}
