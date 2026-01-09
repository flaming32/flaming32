import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowLeft, ArrowRight, Loader2, Smartphone, Battery, Shield } from "lucide-react";
import { Button } from "@/components/ui/button";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const conditionOptions = {
  screen: [
    { value: "excellent", label: "Excellent", desc: "No scratches, perfect display" },
    { value: "good", label: "Good", desc: "Minor scratches, not visible when on" },
    { value: "fair", label: "Fair", desc: "Visible scratches or minor cracks" },
    { value: "poor", label: "Poor", desc: "Cracked or damaged display" },
  ],
  battery: [
    { value: "excellent", label: "Excellent", desc: "90-100% health" },
    { value: "good", label: "Good", desc: "80-89% health" },
    { value: "fair", label: "Fair", desc: "70-79% health" },
    { value: "poor", label: "Poor", desc: "Below 70% health" },
  ],
  damage: [
    { value: "none", label: "None", desc: "No physical damage" },
    { value: "minor", label: "Minor", desc: "Small dents or scratches" },
    { value: "moderate", label: "Moderate", desc: "Noticeable dents or cracks" },
    { value: "severe", label: "Severe", desc: "Major damage affecting use" },
  ],
};

export default function EstimatePage({ phoneData, scrapedPrices, setEstimate }) {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  const [condition, setCondition] = useState({
    screen_condition: "",
    battery_health: "",
    physical_damage: "",
  });

  useEffect(() => {
    if (!phoneData) {
      navigate("/");
    }
  }, [phoneData, navigate]);

  if (!phoneData) return null;

  const steps = [
    { key: "screen_condition", title: "Screen Condition", icon: Smartphone, options: conditionOptions.screen },
    { key: "battery_health", title: "Battery Health", icon: Battery, options: conditionOptions.battery },
    { key: "physical_damage", title: "Physical Damage", icon: Shield, options: conditionOptions.damage },
  ];

  const currentStepData = steps[currentStep];

  const handleConditionChange = (value) => {
    setCondition({ ...condition, [currentStepData.key]: value });
  };

  const handleNext = () => {
    if (!condition[currentStepData.key]) {
      toast.error("Please select an option");
      return;
    }
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      submitEstimate();
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    } else {
      navigate("/");
    }
  };

  const submitEstimate = async () => {
    setIsSubmitting(true);
    
    try {
      // Get average prices from scraped data
      const slotPrices = scrapedPrices?.slot_prices || [];
      const jijiPrices = scrapedPrices?.jiji_prices || [];
      
      const slotAvg = slotPrices.length > 0 
        ? slotPrices.reduce((sum, p) => sum + (p.price || 0), 0) / slotPrices.length 
        : null;
      
      const jijiPriceList = jijiPrices.map(p => p.price).filter(p => p);

      const response = await axios.post(`${API}/estimate-price`, {
        brand: phoneData.brand,
        model: phoneData.model,
        condition: condition,
        slot_price: slotAvg,
        jiji_prices: jijiPriceList,
      });

      setEstimate(response.data);
      toast.success("Estimate calculated!");
      navigate("/results");
    } catch (error) {
      console.error("Estimate error:", error);
      toast.error("Failed to calculate estimate");
    } finally {
      setIsSubmitting(false);
    }
  };

  const formatPrice = (price) => {
    if (!price) return "N/A";
    return `₦${price.toLocaleString()}`;
  };

  // Calculate average prices for display
  const slotAvg = scrapedPrices?.slot_prices?.length > 0
    ? scrapedPrices.slot_prices.reduce((sum, p) => sum + (p.price || 0), 0) / scrapedPrices.slot_prices.length
    : null;
  
  const jijiAvg = scrapedPrices?.jiji_prices?.length > 0
    ? scrapedPrices.jiji_prices.reduce((sum, p) => sum + (p.price || 0), 0) / scrapedPrices.jiji_prices.length
    : null;

  const Icon = currentStepData.icon;

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
        
        {/* Step Indicators */}
        <div className="flex gap-2">
          {steps.map((step, index) => (
            <div
              key={step.key}
              className={`step-indicator ${
                index === currentStep ? "active" : index < currentStep ? "completed" : ""
              }`}
            >
              {index + 1}
            </div>
          ))}
        </div>
      </header>

      <main className="flex-1 flex">
        {/* Left Panel - Phone Info */}
        <div className="hidden lg:flex w-1/3 bg-zinc-950 border-r border-zinc-900 p-8 flex-col">
          <div className="flex-1">
            <div className="font-mono text-xs uppercase tracking-widest text-zinc-500 mb-4">
              Your Phone
            </div>
            
            <h2 className="font-headings font-bold text-3xl mb-2">
              {phoneData.brand}
            </h2>
            <p className="font-headings text-xl text-zinc-400 mb-8">
              {phoneData.model}
            </p>

            {/* Price References */}
            <div className="space-y-4">
              <div className="p-4 border border-zinc-800">
                <div className="font-mono text-xs uppercase tracking-widest text-zinc-500 mb-2">
                  Slot.ng (New)
                </div>
                <div className="price-display text-2xl">
                  {formatPrice(slotAvg)}
                </div>
                <div className="font-mono text-xs text-zinc-600 mt-1">
                  {scrapedPrices?.slot_prices?.length || 0} listings found
                </div>
              </div>

              <div className="p-4 border border-zinc-800">
                <div className="font-mono text-xs uppercase tracking-widest text-zinc-500 mb-2">
                  Jiji.ng (Used)
                </div>
                <div className="price-display text-2xl">
                  {formatPrice(jijiAvg)}
                </div>
                <div className="font-mono text-xs text-zinc-600 mt-1">
                  {scrapedPrices?.jiji_prices?.length || 0} listings found
                </div>
              </div>
            </div>
          </div>

          {/* Selected Conditions */}
          <div className="mt-8 pt-8 border-t border-zinc-800">
            <div className="font-mono text-xs uppercase tracking-widest text-zinc-500 mb-4">
              Condition Summary
            </div>
            <div className="space-y-2 font-mono text-sm">
              {condition.screen_condition && (
                <div className="flex justify-between">
                  <span className="text-zinc-500">Screen:</span>
                  <span className="capitalize">{condition.screen_condition}</span>
                </div>
              )}
              {condition.battery_health && (
                <div className="flex justify-between">
                  <span className="text-zinc-500">Battery:</span>
                  <span className="capitalize">{condition.battery_health}</span>
                </div>
              )}
              {condition.physical_damage && (
                <div className="flex justify-between">
                  <span className="text-zinc-500">Damage:</span>
                  <span className="capitalize">{condition.physical_damage}</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right Panel - Form */}
        <div className="flex-1 flex flex-col p-6 md:p-12">
          <motion.div
            key={currentStep}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.3 }}
            className="flex-1"
          >
            <div className="max-w-xl">
              <div className="flex items-center gap-4 mb-8">
                <div className="w-12 h-12 border border-zinc-700 flex items-center justify-center">
                  <Icon className="h-6 w-6" strokeWidth={1.5} />
                </div>
                <div>
                  <div className="font-mono text-xs uppercase tracking-widest text-zinc-500">
                    Step {currentStep + 1} of {steps.length}
                  </div>
                  <h1 className="font-headings font-bold text-2xl md:text-3xl">
                    {currentStepData.title}
                  </h1>
                </div>
              </div>

              <RadioGroup
                value={condition[currentStepData.key]}
                onValueChange={handleConditionChange}
                className="space-y-3"
              >
                {currentStepData.options.map((option) => (
                  <div key={option.value}>
                    <Label
                      htmlFor={option.value}
                      className={`flex items-center p-4 border cursor-pointer transition-all ${
                        condition[currentStepData.key] === option.value
                          ? "border-white bg-zinc-900"
                          : "border-zinc-800 hover:border-zinc-600"
                      }`}
                      data-testid={`condition-${currentStepData.key}-${option.value}`}
                    >
                      <RadioGroupItem
                        value={option.value}
                        id={option.value}
                        className="sr-only"
                      />
                      <div className="flex-1">
                        <div className="font-headings font-bold">
                          {option.label}
                        </div>
                        <div className="font-mono text-xs text-zinc-500 mt-1">
                          {option.desc}
                        </div>
                      </div>
                      <div className={`w-4 h-4 border ${
                        condition[currentStepData.key] === option.value
                          ? "bg-white border-white"
                          : "border-zinc-600"
                      }`} />
                    </Label>
                  </div>
                ))}
              </RadioGroup>
            </div>
          </motion.div>

          {/* Mobile Price Info */}
          <div className="lg:hidden mb-6 p-4 border border-zinc-800">
            <div className="font-mono text-xs uppercase tracking-widest text-zinc-500 mb-2">
              {phoneData.brand} {phoneData.model}
            </div>
            <div className="flex justify-between font-mono text-sm">
              <span>New: {formatPrice(slotAvg)}</span>
              <span>Used: {formatPrice(jijiAvg)}</span>
            </div>
          </div>

          {/* Navigation Buttons */}
          <div className="flex justify-between mt-8">
            <Button
              variant="outline"
              onClick={handleBack}
              className="bg-transparent border-zinc-700 hover:border-white hover:bg-transparent rounded-none h-12 px-6 font-mono uppercase tracking-wider text-sm"
              data-testid="back-btn"
            >
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back
            </Button>

            <Button
              onClick={handleNext}
              disabled={!condition[currentStepData.key] || isSubmitting}
              className="bg-white text-black hover:bg-zinc-200 rounded-none h-12 px-8 font-mono uppercase tracking-wider text-sm disabled:opacity-50"
              data-testid="next-btn"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Calculating...
                </>
              ) : currentStep === steps.length - 1 ? (
                "Get Estimate"
              ) : (
                <>
                  Next
                  <ArrowRight className="ml-2 h-4 w-4" />
                </>
              )}
            </Button>
          </div>
        </div>
      </main>
    </div>
  );
}
