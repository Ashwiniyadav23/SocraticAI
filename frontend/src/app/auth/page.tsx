"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import api from "@/lib/api";
import { Loader2 } from "lucide-react";
import { motion } from "framer-motion";
import { useGoogleLogin } from "@react-oauth/google";
import { useAuthStore } from "@/store/authStore";

export default function AuthPage() {
  const router = useRouter();
  const login = useAuthStore((state) => state.login);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const googleLogin = useGoogleLogin({
    onSuccess: async (tokenResponse) => {
      console.log("[OAUTH TRACE] SUCCESS - Token Response:", tokenResponse);
      setGoogleLoading(true);
      try {
        console.log("[OAUTH TRACE] Sending token to backend POST /v1/auth/google...");
        const { data } = await api.post("/v1/auth/google", { token: tokenResponse.access_token });
        console.log("[OAUTH TRACE] Backend responded successfully:", data);
        
        // Fetch real user details
        const userResp = await api.get("/v1/auth/me", {
          headers: { Authorization: `Bearer ${data.access_token}` }
        });
        
        const realUser = userResp.data;
        login({ id: realUser.id, email: realUser.email, username: realUser.email.split("@")[0], role: realUser.role }, data.access_token);
        
        toast.success("Google Login successful!");
        router.push("/chat");
      } catch (error: any) {
        console.error("[OAUTH TRACE] Backend Error:", error.response?.data || error.message);
        toast.error(error.response?.data?.detail || "Google authentication failed");
      } finally {
        setGoogleLoading(false);
      }
    },
    onError: (errorResponse) => {
      console.error("[OAUTH TRACE] ERROR - OAuth Flow Failed:", errorResponse);
      toast.error("Google Login Failed");
    },
    onNonOAuthError: (nonOAuthError) => {
      console.error("[OAUTH TRACE] NON-OAUTH ERROR (e.g. Popup Closed, COOP Block):", nonOAuthError);
      toast.error("Google popup was closed or blocked.");
    },
  });

  const triggerGoogleLogin = () => {
    console.log("[OAUTH TRACE] User clicked 'Continue with Google'. Opening popup...");
    googleLogin();
  };

  const handleAuth = async (type: "login" | "register") => {
    setLoading(true);
    try {
      if (type === "register") {
        await api.post("/v1/auth/register", { email, password, role: "student" });
        toast.success("Account created successfully. Please log in.");
      } else {
        const { data } = await api.post("/v1/auth/login", { email, password });
        
        // Fetch real user details
        const userResp = await api.get("/v1/auth/me", {
          headers: { Authorization: `Bearer ${data.access_token}` }
        });
        
        const realUser = userResp.data;
        login({ id: realUser.id, email: realUser.email, username: realUser.email.split("@")[0], role: realUser.role }, data.access_token);
        
        toast.success("Logged in successfully!");
        router.push("/chat");
      }
    } catch (error: any) {
      toast.error(error.response?.data?.detail || "Authentication failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex bg-[#FAFAFC]">
      {/* LEFT SIDE - Auth Card (45%) */}
      <div className="w-full lg:w-[45%] flex flex-col justify-center px-8 sm:px-16 lg:px-24 xl:px-32 relative z-10">
        <motion.div 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="mb-8"
        >
          <div className="flex items-center gap-2 mb-2">
            <div className="w-8 h-8 rounded-lg bg-[#5B5FEF] flex items-center justify-center text-white font-bold text-xl shadow-md">A</div>
            <span className="text-2xl font-semibold tracking-tight text-gray-900">Astra</span>
          </div>
          <p className="text-[#6B7280] font-medium text-sm">Your AI Behavioral Learning Companion</p>
        </motion.div>

        <motion.div 
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="mb-8"
        >
          <h1 className="text-4xl font-bold tracking-tight text-gray-900 mb-2">Welcome to Astra</h1>
          <p className="text-[#6B7280] text-balance">Learn independently. Think deeply. Grow consistently.</p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          <Tabs defaultValue="login" className="w-full max-w-md">
            <TabsList className="grid w-full grid-cols-2 mb-6">
              <TabsTrigger value="login" className="transition-all">Login</TabsTrigger>
              <TabsTrigger value="register" className="transition-all">Sign up</TabsTrigger>
            </TabsList>
            
            <TabsContent value="login">
              <Card className="border border-[#E8EAF5]/50 shadow-xl shadow-[#5B5FEF]/5 bg-white/80 backdrop-blur-xl transition-all duration-300 hover:shadow-2xl hover:shadow-[#5B5FEF]/10">
                <CardContent className="pt-6">
                  <Button 
                    variant="outline" 
                    className="w-full mb-6 py-6 font-medium active:scale-[0.98] transition-transform" 
                    aria-label="Continue with Google"
                    onClick={() => triggerGoogleLogin()}
                    disabled={googleLoading}
                  >
                    {googleLoading ? (
                      <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                    ) : (
                      <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24" aria-hidden="true">
                        <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                        <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                        <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                        <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
                      </svg>
                    )}
                    Continue with Google
                  </Button>
                  
                  <div className="relative mb-6">
                    <div className="absolute inset-0 flex items-center">
                      <span className="w-full border-t border-[#E8EAF5]" />
                    </div>
                    <div className="relative flex justify-center text-xs uppercase tracking-wider">
                      <span className="bg-white px-2 text-[#6B7280]">or continue with email</span>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="email">Email</Label>
                      <Input id="email" type="email" placeholder="student@university.edu" value={email} onChange={(e) => setEmail(e.target.value)} className="focus-visible:ring-[#5B5FEF]" />
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <Label htmlFor="password">Password</Label>
                        <a href="#" className="text-sm font-medium text-[#5B5FEF] hover:text-[#4A4ED8] hover:underline transition-colors">Forgot password?</a>
                      </div>
                      <Input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} className="focus-visible:ring-[#5B5FEF]" />
                    </div>
                    <Button 
                      className="w-full bg-[#5B5FEF] hover:bg-[#4A4ED8] text-white py-6 text-md mt-4 active:scale-[0.98] transition-all shadow-md shadow-[#5B5FEF]/20" 
                      onClick={() => handleAuth("login")} 
                      disabled={loading}
                    >
                      {loading ? (
                        <>
                          <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                          Logging in...
                        </>
                      ) : "Login"}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="register">
              <Card className="border border-[#E8EAF5]/50 shadow-xl shadow-[#5B5FEF]/5 bg-white/80 backdrop-blur-xl transition-all duration-300 hover:shadow-2xl hover:shadow-[#5B5FEF]/10">
                <CardContent className="pt-6">
                  <Button 
                    variant="outline" 
                    className="w-full mb-6 py-6 font-medium active:scale-[0.98] transition-transform" 
                    aria-label="Continue with Google"
                    onClick={() => triggerGoogleLogin()}
                    disabled={googleLoading}
                  >
                    {googleLoading ? (
                      <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                    ) : (
                      <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24" aria-hidden="true">
                        <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                        <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                        <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                        <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
                      </svg>
                    )}
                    Continue with Google
                  </Button>
                  
                  <div className="relative mb-6">
                    <div className="absolute inset-0 flex items-center">
                      <span className="w-full border-t border-[#E8EAF5]" />
                    </div>
                    <div className="relative flex justify-center text-xs uppercase tracking-wider">
                      <span className="bg-white px-2 text-[#6B7280]">or register with email</span>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="reg-email">Email</Label>
                      <Input id="reg-email" type="email" placeholder="student@university.edu" value={email} onChange={(e) => setEmail(e.target.value)} className="focus-visible:ring-[#5B5FEF]" />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="reg-password">Password</Label>
                      <Input id="reg-password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} className="focus-visible:ring-[#5B5FEF]" />
                    </div>
                    <Button 
                      className="w-full bg-[#5B5FEF] hover:bg-[#4A4ED8] text-white py-6 text-md mt-4 active:scale-[0.98] transition-all shadow-md shadow-[#5B5FEF]/20" 
                      onClick={() => handleAuth("register")} 
                      disabled={loading}
                    >
                      {loading ? (
                        <>
                          <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                          Creating account...
                        </>
                      ) : "Sign Up"}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </motion.div>
      </div>

      {/* RIGHT SIDE - Illustration (55%) hidden on mobile */}
      <div className="hidden lg:flex w-[55%] bg-gradient-to-br from-white to-[#E8EAF5] relative overflow-hidden flex-col items-center justify-center p-12">
        {/* Placeholder for 3D Illustration */}
        <div className="w-full max-w-lg aspect-square relative z-10 flex items-center justify-center mb-8">
            <motion.div 
              animate={{ scale: [1, 1.05, 1], opacity: [0.5, 0.8, 0.5] }}
              transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
              className="absolute w-[400px] h-[400px] bg-[#5B5FEF]/10 rounded-full blur-3xl"
            ></motion.div>
            <motion.div 
              animate={{ scale: [1, 1.1, 1], opacity: [0.4, 0.6, 0.4] }}
              transition={{ duration: 5, repeat: Infinity, ease: "easeInOut", delay: 1 }}
              className="absolute w-[300px] h-[300px] bg-[#8B7CF8]/20 rounded-full blur-2xl"
            ></motion.div>
            <div className="z-20 text-center">
              <div className="w-48 h-48 mx-auto bg-white/50 backdrop-blur-md rounded-full shadow-2xl border border-white/60 flex items-center justify-center mb-12 relative">
                {/* Robot icon placeholder */}
                <svg className="w-24 h-24 text-[#5B5FEF]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M8 9a3 3 0 100-6 3 3 0 000 6zM8 11a6 6 0 016-6h2a6 6 0 016 6v3a6 6 0 01-6 6h-2a6 6 0 01-6-6v-3z" />
                </svg>
                {/* Floating bubbles */}
                <motion.div 
                  animate={{ y: [0, -10, 0] }}
                  transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
                  className="absolute -top-4 -right-4 w-12 h-12 bg-white rounded-full shadow-lg flex items-center justify-center"
                >
                  <span className="text-xl">💡</span>
                </motion.div>
                <motion.div 
                  animate={{ y: [0, -15, 0] }}
                  transition={{ duration: 4, repeat: Infinity, ease: "easeInOut", delay: 0.5 }}
                  className="absolute -bottom-8 -left-8 w-16 h-16 bg-white rounded-full shadow-lg flex items-center justify-center"
                >
                  <span className="text-2xl">📚</span>
                </motion.div>
                <motion.div 
                  animate={{ y: [0, -8, 0] }}
                  transition={{ duration: 2.5, repeat: Infinity, ease: "easeInOut", delay: 1 }}
                  className="absolute top-1/2 -right-12 w-10 h-10 bg-white rounded-full shadow-lg flex items-center justify-center"
                >
                  <span className="text-lg">✨</span>
                </motion.div>
              </div>
            </div>
        </div>

        <motion.div 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1, delay: 0.5 }}
          className="relative z-10 text-center"
        >
          <h2 className="text-3xl font-bold tracking-tight text-gray-900 mb-4">Learn. Think. Reflect. Grow.</h2>
          <p className="text-gray-600 max-w-md mx-auto text-lg text-balance leading-relaxed">
            Astra helps students become independent learners through Socratic questioning and behavioral coaching.
          </p>
        </motion.div>
      </div>
    </div>
  );
}
