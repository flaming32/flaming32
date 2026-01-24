import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowLeft, ArrowRight, Loader2, CheckCircle, SkipForward, Moon, Sun } from "lucide-react";
import { Button } from "@/components/ui/button";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { toast } from "sonner";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function EstimatePage({ phoneData, scrapedPrices, setEstimate, accessCode, theme, toggleTheme }) {
  const navigate = useNavigate();
  const [questions, setQuestions] = useState([]);
  const [biometricType, setBiometricType] = useState("fingerprint");
  const [currentStep, setCurrentStep] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [answers, setAnswers] = useState({});
  const [skippedQuestions, setSkippedQuestions] = useState(new Set());

  const isDark = theme === 'dark';

  useEffect(() => {
    if (!phoneData) {
      navigate("/");
      return;
    }
    if (!accessCode) {
      toast.error("Access code required");
      navigate("/");
      return;
    }
    fetchQuestions();
  }, [phoneData, navigate, accessCode]);

  const fetchQuestions = async () => {
    try {
      const response = await axios.get(`${API}/condition-questions/${phoneData.brand}/${encodeURIComponent(phoneData.model)}`);
      setQuestions(response.data.questions);
      setBiometricType(response.data.biometric_type || "fingerprint");
      
      const initialAnswers = {};
      response.data.questions.forEach(q => {
        initialAnswers[q.id] = "";
      });
      setAnswers(initialAnswers);
    } catch (error) {
      console.error("Failed to fetch questions:", error);
      toast.error("Failed to load assessment questions");
    } finally {
      setIsLoading(false);
    }
  };

  if (!phoneData) return null;

  if (isLoading) {
    return (
      <div className={`min-h-screen flex items-center justify-center ${isDark ? 'bg-zinc-950 text-white' : 'bg-white text-zinc-900'}`}>
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
          <p className={`font-mono text-sm ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>Loading assessment...</p>
        </div>
      </div>
    );
  }

  const currentQuestion = questions[currentStep];
  const progress = ((currentStep + 1) / questions.length) * 100;

  const handleAnswerChange = (value) => {
    setAnswers({ ...answers, [currentQuestion.id]: value });
    // Remove from skipped if user selects an answer
    if (skippedQuestions.has(currentQuestion.id)) {
      const newSkipped = new Set(skippedQuestions);
      newSkipped.delete(currentQuestion.id);
      setSkippedQuestions(newSkipped);
    }
  };

  const handleSkip = () => {
    // Mark as skipped with "not_applicable" value
    setAnswers({ ...answers, [currentQuestion.id]: "not_applicable" });
    setSkippedQuestions(new Set([...skippedQuestions, currentQuestion.id]));
    
    if (currentStep < questions.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      submitEstimate();
    }
  };

  const handleNext = () => {
    if (!answers[currentQuestion.id] && !skippedQuestions.has(currentQuestion.id)) {
      toast.error("Please select an option or skip");
      return;
    }
    if (currentStep < questions.length - 1) {
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
      const newPrices = scrapedPrices?.new_prices || [];
      const usedPrices = scrapedPrices?.used_prices || [];
      
      const newAvg = newPrices.length > 0 
        ? newPrices.reduce((sum, p) => sum + (p.price || 0), 0) / newPrices.length 
        : null;
      
      const usedAvg = usedPrices.length > 0
        ? usedPrices.reduce((sum, p) => sum + (p.price || 0), 0) / usedPrices.length
        : null;

      const response = await axios.post(`${API}/estimate-price`, {
        brand: phoneData.brand,
        model: phoneData.model,
        condition: answers,
        new_price: newAvg,
        used_price: usedAvg,
        access_code: accessCode
      });

      setEstimate(response.data);
      toast.success("Estimate calculated!");
      navigate("/results");
    } catch (error) {
      console.error("Estimate error:", error);
      if (error.response?.status === 403) {
        toast.error(error.response.data.detail || "Access code invalid or exhausted");
        navigate("/");
      } else {
        toast.error("Failed to calculate estimate");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const formatPrice = (price) => {
    if (!price) return "N/A";
    return `₦${price.toLocaleString()}`;
  };

  const newAvg = scrapedPrices?.new_prices?.length > 0
    ? scrapedPrices.new_prices.reduce((sum, p) => sum + (p.price || 0), 0) / scrapedPrices.new_prices.length
    : null;
  
  const usedAvg = scrapedPrices?.used_prices?.length > 0
    ? scrapedPrices.used_prices.reduce((sum, p) => sum + (p.price || 0), 0) / scrapedPrices.used_prices.length
    : null;

  const answeredCount = Object.values(answers).filter(v => v).length;

  // Check if current question can be skipped (has N/A option or is optional)
  const canSkip = currentQuestion.options.some(o => o.value === 'not_applicable') || 
                  ['fingerprint_working', 'face_unlock_working', 'touch_id_working', 'face_id_working', 'back_glass_condition', 'true_tone_working'].includes(currentQuestion.id);

  return (
    <div className={`min-h-screen flex flex-col transition-colors duration-300 ${isDark ? 'bg-zinc-950 text-white' : 'bg-white text-zinc-900'}`}>
      <header className={`w-full p-6 flex justify-between items-center ${isDark ? 'border-b border-zinc-900' : 'border-b border-zinc-200'}`}>
        <button onClick={() => navigate("/")} className="font-brand font-extrabold text-2xl tracking-tighter uppercase hover:opacity-70 transition-opacity">
          Stashorra
        </button>
        
        <div className="flex items-center gap-4">
          <button onClick={toggleTheme} className={`p-2 border ${isDark ? 'border-zinc-700 hover:border-white' : 'border-zinc-300 hover:border-zinc-900'}`}>
            {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </button>
          <span className={`font-mono text-xs ${isDark ? 'text-zinc-500' : 'text-zinc-400'}`}>
            {currentStep + 1} / {questions.length}
          </span>
          <div className={`w-32 h-1 rounded-full overflow-hidden ${isDark ? 'bg-zinc-800' : 'bg-zinc-200'}`}>
            <div className={`h-full transition-all duration-300 ${isDark ? 'bg-white' : 'bg-zinc-900'}`} style={{ width: `${progress}%` }} />
          </div>
        </div>
      </header>

      <main className="flex-1 flex">
        {/* Left Panel */}
        <div className={`hidden lg:flex w-1/3 border-r p-8 flex-col ${isDark ? 'bg-zinc-950 border-zinc-900' : 'bg-zinc-50 border-zinc-200'}`}>
          <div className="flex-1">
            <div className={`font-mono text-xs uppercase tracking-widest mb-4 ${isDark ? 'text-zinc-500' : 'text-zinc-500'}`}>Your Phone</div>
            
            <h2 className="font-headings font-bold text-3xl mb-2">{phoneData.brand}</h2>
            <p className={`font-headings text-xl mb-2 ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>{phoneData.model}</p>
            <span className={`font-mono text-xs px-2 py-1 ${isDark ? 'bg-zinc-800' : 'bg-zinc-200'}`}>
              {phoneData.type === 'iphone' ? 'iPhone' : 'Android'}
              {biometricType === 'face_id' && ' • Face ID'}
              {biometricType === 'touch_id' && ' • Touch ID'}
            </span>

            <div className="space-y-4 mt-8">
              <div className={`p-4 border ${isDark ? 'border-zinc-800' : 'border-zinc-200'}`}>
                <div className={`font-mono text-xs uppercase tracking-widest mb-2 ${isDark ? 'text-zinc-500' : 'text-zinc-500'}`}>New Price</div>
                <div className="price-display text-2xl">{formatPrice(newAvg)}</div>
              </div>
              <div className={`p-4 border ${isDark ? 'border-zinc-800' : 'border-zinc-200'}`}>
                <div className={`font-mono text-xs uppercase tracking-widest mb-2 ${isDark ? 'text-zinc-500' : 'text-zinc-500'}`}>Used Market</div>
                <div className="price-display text-2xl">{formatPrice(usedAvg)}</div>
              </div>
            </div>
          </div>

          <div className={`mt-8 pt-8 border-t ${isDark ? 'border-zinc-800' : 'border-zinc-200'}`}>
            <div className={`font-mono text-xs uppercase tracking-widest mb-4 ${isDark ? 'text-zinc-500' : 'text-zinc-500'}`}>Progress</div>
            <div className="flex items-center gap-2 mb-2">
              <CheckCircle className={`h-4 w-4 ${answeredCount === questions.length ? 'text-green-500' : isDark ? 'text-zinc-600' : 'text-zinc-400'}`} />
              <span className="font-mono text-sm">{answeredCount} of {questions.length} answered</span>
            </div>
            <Progress value={(answeredCount / questions.length) * 100} className="h-1" />
            {skippedQuestions.size > 0 && (
              <div className={`font-mono text-xs mt-2 ${isDark ? 'text-zinc-500' : 'text-zinc-400'}`}>
                {skippedQuestions.size} skipped (N/A)
              </div>
            )}
          </div>
        </div>

        {/* Right Panel */}
        <div className="flex-1 flex flex-col p-6 md:p-12">
          <AnimatePresence mode="wait">
            <motion.div
              key={currentStep}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.3 }}
              className="flex-1"
            >
              <div className="max-w-xl">
                <div className="mb-8">
                  <div className={`font-mono text-xs uppercase tracking-widest mb-2 ${isDark ? 'text-zinc-500' : 'text-zinc-500'}`}>
                    Question {currentStep + 1} of {questions.length}
                  </div>
                  <h1 className="font-headings font-bold text-2xl md:text-3xl mb-2">{currentQuestion.label}</h1>
                  <p className={`text-sm ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>{currentQuestion.description}</p>
                </div>

                <RadioGroup value={answers[currentQuestion.id]} onValueChange={handleAnswerChange} className="space-y-3">
                  {currentQuestion.options.map((option) => (
                    <div key={option.value}>
                      <Label
                        htmlFor={`${currentQuestion.id}-${option.value}`}
                        className={`flex items-center p-4 border cursor-pointer transition-all ${
                          answers[currentQuestion.id] === option.value
                            ? isDark ? "border-white bg-zinc-900" : "border-zinc-900 bg-zinc-100"
                            : isDark ? "border-zinc-800 hover:border-zinc-600" : "border-zinc-200 hover:border-zinc-400"
                        }`}
                        data-testid={`option-${currentQuestion.id}-${option.value}`}
                      >
                        <RadioGroupItem value={option.value} id={`${currentQuestion.id}-${option.value}`} className="sr-only" />
                        <div className="flex-1">
                          <div className="font-headings font-bold">{option.label}</div>
                          <div className={`font-mono text-xs mt-1 ${isDark ? 'text-zinc-500' : 'text-zinc-400'}`}>{option.desc}</div>
                        </div>
                        <div className={`w-4 h-4 border ${
                          answers[currentQuestion.id] === option.value
                            ? isDark ? "bg-white border-white" : "bg-zinc-900 border-zinc-900"
                            : isDark ? "border-zinc-600" : "border-zinc-400"
                        }`} />
                      </Label>
                    </div>
                  ))}
                </RadioGroup>

                {/* Skip Button - Always visible */}
                <div className="mt-4">
                  <button
                    onClick={handleSkip}
                    className={`flex items-center gap-2 font-mono text-xs uppercase tracking-wider py-2 px-4 border transition-colors ${
                      skippedQuestions.has(currentQuestion.id)
                        ? 'bg-yellow-500/20 border-yellow-500/50 text-yellow-500'
                        : isDark ? 'border-zinc-700 text-zinc-400 hover:border-zinc-500 hover:text-zinc-300' : 'border-zinc-300 text-zinc-500 hover:border-zinc-400 hover:text-zinc-700'
                    }`}
                    data-testid="skip-btn"
                  >
                    <SkipForward className="h-4 w-4" />
                    {skippedQuestions.has(currentQuestion.id) ? 'Skipped (N/A)' : "Skip - Phone doesn't have this"}
                  </button>
                </div>
              </div>
            </motion.div>
          </AnimatePresence>

          {/* Mobile Info */}
          <div className={`lg:hidden mb-6 p-4 border ${isDark ? 'border-zinc-800' : 'border-zinc-200'}`}>
            <div className={`font-mono text-xs uppercase tracking-widest mb-2 ${isDark ? 'text-zinc-500' : 'text-zinc-500'}`}>
              {phoneData.brand} {phoneData.model}
            </div>
            <div className="flex justify-between font-mono text-sm">
              <span>New: {formatPrice(newAvg)}</span>
              <span>Used: {formatPrice(usedAvg)}</span>
            </div>
          </div>

          {/* Navigation */}
          <div className="flex justify-between mt-8">
            <Button
              variant="outline"
              onClick={handleBack}
              className={`h-12 px-6 font-mono uppercase tracking-wider text-sm ${isDark ? 'bg-transparent border-zinc-700 hover:border-white' : 'bg-transparent border-zinc-300 hover:border-zinc-900'}`}
            >
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back
            </Button>

            <Button
              onClick={handleNext}
              disabled={(!answers[currentQuestion.id] && !skippedQuestions.has(currentQuestion.id)) || isSubmitting}
              className={`h-12 px-8 font-mono uppercase tracking-wider text-sm disabled:opacity-50 ${isDark ? 'bg-white text-black hover:bg-zinc-200' : 'bg-zinc-900 text-white hover:bg-zinc-800'}`}
            >
              {isSubmitting ? (
                <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Calculating...</>
              ) : currentStep === questions.length - 1 ? (
                "Get Estimate"
              ) : (
                <>Next<ArrowRight className="ml-2 h-4 w-4" /></>
              )}
            </Button>
          </div>
        </div>
      </main>
    </div>
  );
}
