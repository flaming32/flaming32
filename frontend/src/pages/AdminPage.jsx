import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Lock, Plus, Trash2, Copy, LogOut, Loader2, Key, Users } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function AdminPage() {
  const navigate = useNavigate();
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [isLoggingIn, setIsLoggingIn] = useState(false);
  
  const [codes, setCodes] = useState([]);
  const [isLoadingCodes, setIsLoadingCodes] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [newCodeNote, setNewCodeNote] = useState("");

  // Check if admin is already logged in
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

  // Fetch codes when logged in
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
      const response = await axios.get(`${API}/admin/codes`, {
        params: { username, password }
      });
      setCodes(response.data.codes);
    } catch (error) {
      toast.error("Failed to fetch codes");
    } finally {
      setIsLoadingCodes(false);
    }
  };

  const generateCode = async () => {
    setIsGenerating(true);
    try {
      const response = await axios.post(`${API}/admin/generate-code`, 
        { note: newCodeNote },
        { params: { username, password } }
      );
      toast.success(`Code generated: ${response.data.code}`);
      setNewCodeNote("");
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
      await axios.delete(`${API}/admin/code/${code}`, {
        params: { username, password }
      });
      toast.success("Code deleted");
      fetchCodes();
    } catch (error) {
      toast.error("Failed to delete code");
    }
  };

  const copyCode = (code) => {
    navigator.clipboard.writeText(code);
    toast.success("Code copied to clipboard!");
  };

  if (!isLoggedIn) {
    return (
      <div className="min-h-screen flex flex-col">
        <header className="w-full p-6 flex justify-between items-center border-b border-zinc-900">
          <button 
            onClick={() => navigate("/")}
            className="font-brand font-extrabold text-2xl tracking-tighter uppercase hover:text-zinc-400 transition-colors"
          >
            Stashorra
          </button>
        </header>

        <main className="flex-1 flex items-center justify-center p-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="w-full max-w-md"
          >
            <div className="bg-zinc-950 border border-zinc-800 p-8">
              <div className="text-center mb-8">
                <div className="w-16 h-16 mx-auto mb-4 border border-zinc-700 flex items-center justify-center">
                  <Lock className="h-8 w-8" />
                </div>
                <h1 className="font-headings font-bold text-2xl mb-2">Admin Login</h1>
                <p className="text-zinc-400 text-sm">Access the admin dashboard</p>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="font-mono text-xs uppercase tracking-widest text-zinc-500 block mb-2">
                    Username
                  </label>
                  <Input
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className="bg-zinc-900 border-zinc-700 rounded-none h-12"
                    placeholder="Enter username"
                    data-testid="admin-username"
                  />
                </div>

                <div>
                  <label className="font-mono text-xs uppercase tracking-widest text-zinc-500 block mb-2">
                    Password
                  </label>
                  <Input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="bg-zinc-900 border-zinc-700 rounded-none h-12"
                    placeholder="Enter password"
                    onKeyDown={(e) => e.key === 'Enter' && handleLogin()}
                    data-testid="admin-password"
                  />
                </div>

                <Button
                  onClick={handleLogin}
                  disabled={isLoggingIn}
                  className="w-full bg-white text-black hover:bg-zinc-200 rounded-none h-12 font-mono uppercase tracking-wider text-sm"
                  data-testid="admin-login-btn"
                >
                  {isLoggingIn ? (
                    <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Logging in...</>
                  ) : (
                    "Login"
                  )}
                </Button>
              </div>
            </div>
          </motion.div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="w-full p-6 flex justify-between items-center border-b border-zinc-900">
        <button 
          onClick={() => navigate("/")}
          className="font-brand font-extrabold text-2xl tracking-tighter uppercase hover:text-zinc-400 transition-colors"
        >
          Stashorra
        </button>
        
        <div className="flex items-center gap-4">
          <span className="font-mono text-sm text-zinc-400">Admin</span>
          <Button
            variant="outline"
            onClick={handleLogout}
            className="bg-transparent border-zinc-700 hover:border-white rounded-none h-10 px-4"
          >
            <LogOut className="h-4 w-4" />
          </Button>
        </div>
      </header>

      <main className="flex-1 p-6 md:p-12">
        <div className="max-w-4xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
              <div className="bg-zinc-950 border border-zinc-800 p-6">
                <div className="flex items-center gap-3 mb-2">
                  <Key className="h-5 w-5 text-zinc-500" />
                  <span className="font-mono text-xs uppercase tracking-widest text-zinc-500">Total Codes</span>
                </div>
                <div className="font-headings text-3xl font-bold">{codes.length}</div>
              </div>
              
              <div className="bg-zinc-950 border border-zinc-800 p-6">
                <div className="flex items-center gap-3 mb-2">
                  <Users className="h-5 w-5 text-zinc-500" />
                  <span className="font-mono text-xs uppercase tracking-widest text-zinc-500">Active Codes</span>
                </div>
                <div className="font-headings text-3xl font-bold">
                  {codes.filter(c => c.uses_remaining > 0).length}
                </div>
              </div>
              
              <div className="bg-zinc-950 border border-zinc-800 p-6">
                <div className="flex items-center gap-3 mb-2">
                  <span className="font-mono text-xs uppercase tracking-widest text-zinc-500">Total Uses Left</span>
                </div>
                <div className="font-headings text-3xl font-bold">
                  {codes.reduce((sum, c) => sum + (c.uses_remaining || 0), 0)}
                </div>
              </div>
            </div>

            {/* Generate Code */}
            <div className="bg-zinc-950 border border-zinc-800 p-6 mb-8">
              <h2 className="font-headings font-bold text-xl mb-4">Generate Access Code</h2>
              
              <div className="flex gap-4">
                <Input
                  placeholder="Note (optional) - e.g. Customer name"
                  value={newCodeNote}
                  onChange={(e) => setNewCodeNote(e.target.value)}
                  className="bg-zinc-900 border-zinc-700 rounded-none h-12 flex-1"
                  data-testid="code-note-input"
                />
                <Button
                  onClick={generateCode}
                  disabled={isGenerating}
                  className="bg-white text-black hover:bg-zinc-200 rounded-none h-12 px-6 font-mono uppercase tracking-wider text-sm"
                  data-testid="generate-code-btn"
                >
                  {isGenerating ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <><Plus className="mr-2 h-4 w-4" /> Generate</>
                  )}
                </Button>
              </div>
            </div>

            {/* Codes List */}
            <div className="bg-zinc-950 border border-zinc-800">
              <div className="p-6 border-b border-zinc-800 flex justify-between items-center">
                <h2 className="font-headings font-bold text-xl">Access Codes</h2>
                <Button
                  variant="outline"
                  onClick={fetchCodes}
                  disabled={isLoadingCodes}
                  className="bg-transparent border-zinc-700 hover:border-white rounded-none h-10 px-4"
                >
                  {isLoadingCodes ? <Loader2 className="h-4 w-4 animate-spin" /> : "Refresh"}
                </Button>
              </div>

              {isLoadingCodes ? (
                <div className="p-12 text-center">
                  <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
                  <p className="text-zinc-400">Loading codes...</p>
                </div>
              ) : codes.length === 0 ? (
                <div className="p-12 text-center text-zinc-500">
                  No codes generated yet.
                </div>
              ) : (
                <div className="divide-y divide-zinc-800">
                  {codes.map((code) => (
                    <div 
                      key={code.code} 
                      className={`p-4 flex items-center justify-between hover:bg-zinc-900/50 ${
                        code.uses_remaining === 0 ? 'opacity-50' : ''
                      }`}
                    >
                      <div className="flex items-center gap-4">
                        <div 
                          className={`font-mono text-lg font-bold ${
                            code.uses_remaining > 0 ? 'text-green-500' : 'text-zinc-500'
                          }`}
                        >
                          {code.code}
                        </div>
                        <div className="text-sm">
                          <div className="text-zinc-400">
                            {code.uses_remaining} uses remaining
                          </div>
                          {code.note && (
                            <div className="text-zinc-500 text-xs">{code.note}</div>
                          )}
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-2">
                        <Button
                          variant="outline"
                          onClick={() => copyCode(code.code)}
                          className="bg-transparent border-zinc-700 hover:border-white rounded-none h-9 w-9 p-0"
                        >
                          <Copy className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="outline"
                          onClick={() => deleteCode(code.code)}
                          className="bg-transparent border-zinc-700 hover:border-red-500 hover:text-red-500 rounded-none h-9 w-9 p-0"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </motion.div>
        </div>
      </main>
    </div>
  );
}
