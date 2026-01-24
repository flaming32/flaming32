import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Lock, Plus, Trash2, Copy, LogOut, Loader2, Key, Users, Package, Moon, Sun } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function AdminPage({ theme, toggleTheme }) {
  const navigate = useNavigate();
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [isLoggingIn, setIsLoggingIn] = useState(false);
  
  const [codes, setCodes] = useState([]);
  const [isLoadingCodes, setIsLoadingCodes] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [newCodeNote, setNewCodeNote] = useState("");
  const [selectedPackage, setSelectedPackage] = useState("basic");
  const [sendEmail, setSendEmail] = useState(false);
  const [recipientEmail, setRecipientEmail] = useState("");

  const isDark = theme === 'dark';

  useEffect(() => {
    const savedAuth = localStorage.getItem('stashorra_admin_auth');
    if (savedAuth) {
      try {
        const auth = JSON.parse(savedAuth);
        setUsername(auth.username);
        setPassword(auth.password);
        setIsLoggedIn(true);
      } catch (e) {
        localStorage.removeItem('stashorra_admin_auth');
      }
    }
  }, []);

  useEffect(() => {
    if (isLoggedIn && username && password) {
      fetchCodes();
    }
  }, [isLoggedIn]);

  const handleLogin = async () => {
    if (!username || !password) {
      toast.error("Please enter username and password");
      return;
    }
    setIsLoggingIn(true);
    try {
      const response = await axios.post(`${API}/admin/login`, { username, password });
      if (response.data.success) {
        setIsLoggedIn(true);
        localStorage.setItem('stashorra_admin_auth', JSON.stringify({ username, password }));
        toast.success("Login successful!");
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || "Invalid credentials");
    } finally {
      setIsLoggingIn(false);
    }
  };

  const handleLogout = () => {
    setIsLoggedIn(false);
    setUsername("");
    setPassword("");
    setCodes([]);
    localStorage.removeItem('stashorra_admin_auth');
    toast.success("Logged out");
  };

  const fetchCodes = async () => {
    setIsLoadingCodes(true);
    try {
      const response = await axios.get(`${API}/admin/codes`, { params: { username, password } });
      setCodes(response.data.codes);
    } catch (error) {
      toast.error("Failed to fetch codes");
    } finally {
      setIsLoadingCodes(false);
    }
  };

  const generateCode = async (packageType) => {
    setIsGenerating(true);
    try {
      const response = await axios.post(`${API}/admin/generate-code`, {
        username,
        password,
        note: newCodeNote,
        package: packageType,
        send_email: sendEmail,
        recipient_email: sendEmail ? recipientEmail : null
      });
      toast.success(`Code generated: ${response.data.code}`);
      if (response.data.email_sent) {
        toast.success(`Email sent to ${recipientEmail}`);
      }
      setNewCodeNote("");
      setRecipientEmail("");
      setSendEmail(false);
      fetchCodes();
    } catch (error) {
      toast.error("Failed to generate code");
    } finally {
      setIsGenerating(false);
    }
  };

  const deleteCode = async (code) => {
    if (!confirm(`Delete code ${code}?`)) return;
    try {
      await axios.delete(`${API}/admin/code/${code}`, { params: { username, password } });
      toast.success("Code deleted");
      fetchCodes();
    } catch (error) {
      toast.error("Failed to delete code");
    }
  };

  const copyCode = (code) => {
    navigator.clipboard.writeText(code);
    toast.success("Code copied!");
  };

  // Separate codes by package type
  const basicCodes = codes.filter(c => c.package === 'basic' || !c.package);
  const resellerCodes = codes.filter(c => c.package === 'reseller');

  // Stats
  const totalBasicUses = basicCodes.reduce((sum, c) => sum + (c.uses_remaining || 0), 0);
  const totalResellerUses = resellerCodes.reduce((sum, c) => sum + (c.uses_remaining || 0), 0);

  if (!isLoggedIn) {
    return (
      <div className={`min-h-screen flex flex-col ${isDark ? 'bg-zinc-950 text-white' : 'bg-white text-zinc-900'}`}>
        <header className={`w-full p-6 flex justify-between items-center ${isDark ? '' : 'border-b border-zinc-200'}`}>
          <button onClick={() => navigate("/")} className="font-brand font-extrabold text-2xl tracking-tighter uppercase hover:opacity-70 transition-opacity">
            Stashorra
          </button>
          <button onClick={toggleTheme} className={`p-2 border ${isDark ? 'border-zinc-700 hover:border-white' : 'border-zinc-300 hover:border-zinc-900'}`}>
            {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </button>
        </header>

        <main className="flex-1 flex items-center justify-center p-4">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-md">
            <div className={`border p-8 ${isDark ? 'bg-zinc-950 border-zinc-800' : 'bg-zinc-50 border-zinc-200'}`}>
              <div className="text-center mb-8">
                <div className={`w-16 h-16 mx-auto mb-4 border flex items-center justify-center ${isDark ? 'border-zinc-700' : 'border-zinc-300'}`}>
                  <Lock className="h-8 w-8" />
                </div>
                <h1 className="font-headings font-bold text-2xl mb-2">Admin Login</h1>
                <p className={isDark ? 'text-zinc-400 text-sm' : 'text-zinc-600 text-sm'}>Access the admin dashboard</p>
              </div>

              <div className="space-y-4">
                <div>
                  <label className={`font-mono text-xs uppercase tracking-widest block mb-2 ${isDark ? 'text-zinc-500' : 'text-zinc-500'}`}>Username</label>
                  <Input type="text" value={username} onChange={(e) => setUsername(e.target.value)} className={`h-12 ${isDark ? 'bg-zinc-900 border-zinc-700' : 'bg-white border-zinc-300'}`} placeholder="Enter username" data-testid="admin-username" />
                </div>
                <div>
                  <label className={`font-mono text-xs uppercase tracking-widest block mb-2 ${isDark ? 'text-zinc-500' : 'text-zinc-500'}`}>Password</label>
                  <Input type="password" value={password} onChange={(e) => setPassword(e.target.value)} className={`h-12 ${isDark ? 'bg-zinc-900 border-zinc-700' : 'bg-white border-zinc-300'}`} placeholder="Enter password" onKeyDown={(e) => e.key === 'Enter' && handleLogin()} data-testid="admin-password" />
                </div>
                <Button onClick={handleLogin} disabled={isLoggingIn} className={`w-full h-12 font-mono uppercase tracking-wider text-sm ${isDark ? 'bg-white text-black hover:bg-zinc-200' : 'bg-zinc-900 text-white hover:bg-zinc-800'}`} data-testid="admin-login-btn">
                  {isLoggingIn ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Logging in...</> : "Login"}
                </Button>
              </div>
            </div>
          </motion.div>
        </main>
      </div>
    );
  }

  const CodeCard = ({ code, isDark }) => (
    <div className={`p-4 flex items-center justify-between ${code.uses_remaining === 0 ? 'opacity-50' : ''} ${isDark ? 'hover:bg-zinc-900/50' : 'hover:bg-zinc-50'}`}>
      <div className="flex items-center gap-4">
        <div className={`font-mono text-lg font-bold ${code.uses_remaining > 0 ? 'text-green-500' : isDark ? 'text-zinc-500' : 'text-zinc-400'}`}>
          {code.code}
        </div>
        <div className="text-sm">
          <div className={isDark ? 'text-zinc-400' : 'text-zinc-600'}>{code.uses_remaining} uses left</div>
          {code.note && <div className={`text-xs ${isDark ? 'text-zinc-500' : 'text-zinc-400'}`}>{code.note}</div>}
        </div>
      </div>
      <div className="flex items-center gap-2">
        <Button variant="outline" onClick={() => copyCode(code.code)} className={`h-9 w-9 p-0 ${isDark ? 'bg-transparent border-zinc-700 hover:border-white' : 'bg-transparent border-zinc-300 hover:border-zinc-900'}`}>
          <Copy className="h-4 w-4" />
        </Button>
        <Button variant="outline" onClick={() => deleteCode(code.code)} className={`h-9 w-9 p-0 ${isDark ? 'bg-transparent border-zinc-700 hover:border-red-500 hover:text-red-500' : 'bg-transparent border-zinc-300 hover:border-red-500 hover:text-red-500'}`}>
          <Trash2 className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );

  return (
    <div className={`min-h-screen flex flex-col ${isDark ? 'bg-zinc-950 text-white' : 'bg-white text-zinc-900'}`}>
      {/* Header */}
      <header className={`w-full p-6 flex justify-between items-center ${isDark ? 'border-b border-zinc-900' : 'border-b border-zinc-200'}`}>
        <button onClick={() => navigate("/")} className="font-brand font-extrabold text-2xl tracking-tighter uppercase hover:opacity-70 transition-opacity">
          Stashorra
        </button>
        <div className="flex items-center gap-4">
          <span className={`font-mono text-sm ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>Admin</span>
          <button onClick={toggleTheme} className={`p-2 border ${isDark ? 'border-zinc-700 hover:border-white' : 'border-zinc-300 hover:border-zinc-900'}`}>
            {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </button>
          <Button variant="outline" onClick={handleLogout} className={`h-10 px-4 ${isDark ? 'bg-transparent border-zinc-700 hover:border-white' : 'bg-transparent border-zinc-300 hover:border-zinc-900'}`}>
            <LogOut className="h-4 w-4" />
          </Button>
        </div>
      </header>

      <main className="flex-1 p-6 md:p-12">
        <div className="max-w-6xl mx-auto">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
              <div className={`border p-6 ${isDark ? 'bg-zinc-950 border-zinc-800' : 'bg-zinc-50 border-zinc-200'}`}>
                <div className="flex items-center gap-3 mb-2">
                  <Key className={`h-5 w-5 ${isDark ? 'text-zinc-500' : 'text-zinc-400'}`} />
                  <span className={`font-mono text-xs uppercase tracking-widest ${isDark ? 'text-zinc-500' : 'text-zinc-500'}`}>Total Codes</span>
                </div>
                <div className="font-headings text-3xl font-bold">{codes.length}</div>
              </div>
              <div className={`border p-6 ${isDark ? 'bg-zinc-950 border-zinc-800' : 'bg-zinc-50 border-zinc-200'}`}>
                <div className="flex items-center gap-3 mb-2">
                  <Users className={`h-5 w-5 ${isDark ? 'text-zinc-500' : 'text-zinc-400'}`} />
                  <span className={`font-mono text-xs uppercase tracking-widest ${isDark ? 'text-zinc-500' : 'text-zinc-500'}`}>Basic Codes</span>
                </div>
                <div className="font-headings text-3xl font-bold">{basicCodes.length}</div>
                <div className={`text-xs font-mono ${isDark ? 'text-zinc-500' : 'text-zinc-400'}`}>{totalBasicUses} uses left</div>
              </div>
              <div className={`border p-6 ${isDark ? 'bg-zinc-950 border-zinc-800' : 'bg-zinc-50 border-zinc-200'}`}>
                <div className="flex items-center gap-3 mb-2">
                  <Package className={`h-5 w-5 text-green-500`} />
                  <span className={`font-mono text-xs uppercase tracking-widest ${isDark ? 'text-zinc-500' : 'text-zinc-500'}`}>Reseller Codes</span>
                </div>
                <div className="font-headings text-3xl font-bold text-green-500">{resellerCodes.length}</div>
                <div className={`text-xs font-mono ${isDark ? 'text-zinc-500' : 'text-zinc-400'}`}>{totalResellerUses} uses left</div>
              </div>
              <div className={`border p-6 ${isDark ? 'bg-zinc-950 border-zinc-800' : 'bg-zinc-50 border-zinc-200'}`}>
                <div className="flex items-center gap-3 mb-2">
                  <span className={`font-mono text-xs uppercase tracking-widest ${isDark ? 'text-zinc-500' : 'text-zinc-500'}`}>Total Uses</span>
                </div>
                <div className="font-headings text-3xl font-bold">{totalBasicUses + totalResellerUses}</div>
              </div>
            </div>

            {/* Generate Code */}
            <div className={`border p-6 mb-8 ${isDark ? 'bg-zinc-950 border-zinc-800' : 'bg-zinc-50 border-zinc-200'}`}>
              <h2 className="font-headings font-bold text-xl mb-4">Generate Access Code</h2>
              
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Input placeholder="Note (optional) - e.g. Customer name" value={newCodeNote} onChange={(e) => setNewCodeNote(e.target.value)} className={`h-12 ${isDark ? 'bg-zinc-900 border-zinc-700' : 'bg-white border-zinc-300'}`} data-testid="code-note-input" />
                  <div className="flex gap-2">
                    <label className={`flex items-center gap-2 cursor-pointer ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
                      <input type="checkbox" checked={sendEmail} onChange={(e) => setSendEmail(e.target.checked)} className="w-4 h-4" />
                      <span className="font-mono text-xs">Send via email</span>
                    </label>
                    {sendEmail && (
                      <Input placeholder="Email address" value={recipientEmail} onChange={(e) => setRecipientEmail(e.target.value)} className={`h-10 flex-1 ${isDark ? 'bg-zinc-900 border-zinc-700' : 'bg-white border-zinc-300'}`} />
                    )}
                  </div>
                </div>
                
                <div className="flex gap-4">
                  <Button onClick={() => generateCode("basic")} disabled={isGenerating} className={`flex-1 h-12 font-mono uppercase tracking-wider text-sm ${isDark ? 'bg-zinc-800 text-white hover:bg-zinc-700 border border-zinc-700' : 'bg-zinc-200 text-zinc-900 hover:bg-zinc-300 border border-zinc-300'}`}>
                    {isGenerating ? <Loader2 className="h-4 w-4 animate-spin" /> : <><Plus className="mr-2 h-4 w-4" /> Basic (2 uses)</>}
                  </Button>
                  <Button onClick={() => generateCode("reseller")} disabled={isGenerating} className="flex-1 h-12 font-mono uppercase tracking-wider text-sm bg-green-600 text-white hover:bg-green-700" data-testid="generate-reseller-btn">
                    {isGenerating ? <Loader2 className="h-4 w-4 animate-spin" /> : <><Package className="mr-2 h-4 w-4" /> Reseller (20 uses)</>}
                  </Button>
                </div>
              </div>
            </div>

            {/* Two Column Layout for Codes */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Basic Codes Section */}
              <div className={`border ${isDark ? 'bg-zinc-950 border-zinc-800' : 'bg-zinc-50 border-zinc-200'}`}>
                <div className={`p-6 flex justify-between items-center ${isDark ? 'border-b border-zinc-800' : 'border-b border-zinc-200'}`}>
                  <div>
                    <h2 className="font-headings font-bold text-xl flex items-center gap-2">
                      <Users className="h-5 w-5" /> Basic Codes
                    </h2>
                    <p className={`font-mono text-xs mt-1 ${isDark ? 'text-zinc-500' : 'text-zinc-400'}`}>₦400 / 2 uses each</p>
                  </div>
                  <span className={`font-mono text-sm ${isDark ? 'text-zinc-500' : 'text-zinc-400'}`}>{basicCodes.length} codes</span>
                </div>

                {isLoadingCodes ? (
                  <div className="p-12 text-center">
                    <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
                  </div>
                ) : basicCodes.length === 0 ? (
                  <div className={`p-12 text-center ${isDark ? 'text-zinc-500' : 'text-zinc-400'}`}>No basic codes yet.</div>
                ) : (
                  <div className={`divide-y max-h-[400px] overflow-y-auto ${isDark ? 'divide-zinc-800' : 'divide-zinc-200'}`}>
                    {basicCodes.map((code) => <CodeCard key={code.code} code={code} isDark={isDark} />)}
                  </div>
                )}
              </div>

              {/* Reseller Codes Section */}
              <div className={`border border-green-500/30 ${isDark ? 'bg-zinc-950' : 'bg-green-50/30'}`}>
                <div className={`p-6 flex justify-between items-center ${isDark ? 'border-b border-green-500/30 bg-green-500/5' : 'border-b border-green-200 bg-green-100/50'}`}>
                  <div>
                    <h2 className="font-headings font-bold text-xl flex items-center gap-2 text-green-500">
                      <Package className="h-5 w-5" /> Reseller Codes
                    </h2>
                    <p className={`font-mono text-xs mt-1 ${isDark ? 'text-zinc-500' : 'text-zinc-400'}`}>₦3,000 / 20 uses each</p>
                  </div>
                  <span className="font-mono text-sm text-green-500">{resellerCodes.length} codes</span>
                </div>

                {isLoadingCodes ? (
                  <div className="p-12 text-center">
                    <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
                  </div>
                ) : resellerCodes.length === 0 ? (
                  <div className={`p-12 text-center ${isDark ? 'text-zinc-500' : 'text-zinc-400'}`}>No reseller codes yet.</div>
                ) : (
                  <div className={`divide-y max-h-[400px] overflow-y-auto ${isDark ? 'divide-zinc-800' : 'divide-zinc-200'}`}>
                    {resellerCodes.map((code) => <CodeCard key={code.code} code={code} isDark={isDark} />)}
                  </div>
                )}
              </div>
            </div>

            {/* Refresh Button */}
            <div className="mt-6 text-center">
              <Button variant="outline" onClick={fetchCodes} disabled={isLoadingCodes} className={`h-10 px-6 ${isDark ? 'bg-transparent border-zinc-700 hover:border-white' : 'bg-transparent border-zinc-300 hover:border-zinc-900'}`}>
                {isLoadingCodes ? <Loader2 className="h-4 w-4 animate-spin" /> : "Refresh Codes"}
              </Button>
            </div>
          </motion.div>
        </div>
      </main>
    </div>
  );
}
