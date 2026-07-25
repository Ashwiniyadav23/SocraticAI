"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import api from "@/lib/api";
import { Loader2, ShieldAlert } from "lucide-react";
import { motion } from "framer-motion";
import { useAuthStore } from "@/store/authStore";

export default function AdminLoginPage() {
  const router = useRouter();
  const login = useAuthStore((state) => state.login);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const handleAdminLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      toast.error("Please fill in all fields.");
      return;
    }

    setLoading(true);
    try {
      // 1. Authenticate credentials
      const { data } = await api.post("/v1/auth/login", { email, password });
      
      // 2. Fetch user profile
      const userResp = await api.get("/v1/auth/me", {
        headers: { Authorization: `Bearer ${data.access_token}` }
      });
      
      const loggedUser = userResp.data;

      // 3. Enforce Admin Role
      if (loggedUser.role !== "admin") {
        toast.error("Access denied. Admin credentials required.");
        setLoading(false);
        return;
      }

      // 4. Update auth state and redirect
      login(
        {
          id: loggedUser.id,
          email: loggedUser.email,
          username: loggedUser.email.split("@")[0],
          role: loggedUser.role,
          status: loggedUser.status
        },
        data.access_token
      );
      
      toast.success("Administrator login successful!");
      router.push("/admin");
    } catch (error: any) {
      const errMsg = error.response?.data?.detail || "Authentication failed. Please verify credentials.";
      toast.error(errMsg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-[#0F172A] via-[#1E293B] to-[#0F172A] p-6 relative overflow-hidden">
      {/* Decorative premium background blobs */}
      <motion.div
        animate={{ scale: [1, 1.15, 1], opacity: [0.3, 0.45, 0.3] }}
        transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
        className="absolute top-1/4 left-1/4 w-[350px] h-[350px] bg-[#5B5FEF]/10 rounded-full blur-3xl"
      ></motion.div>
      <motion.div
        animate={{ scale: [1, 1.1, 1], opacity: [0.2, 0.35, 0.2] }}
        transition={{ duration: 7, repeat: Infinity, ease: "easeInOut", delay: 1 }}
        className="absolute bottom-1/4 right-1/4 w-[300px] h-[300px] bg-[#8B7CF8]/10 rounded-full blur-3xl"
      ></motion.div>

      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-md relative z-10"
      >
        <div className="flex flex-col items-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-[#5B5FEF] to-[#8B7CF8] flex items-center justify-center text-white font-bold text-2xl shadow-lg shadow-[#5B5FEF]/20 mb-4">
            A
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white mb-2">Astra Admin Portal</h1>
          <p className="text-[#94A3B8] text-sm font-medium">Log in to manage coaches, students, and platform stats.</p>
        </div>

        <div className="bg-[#1E293B]/70 border border-[#334155]/60 backdrop-blur-2xl rounded-3xl shadow-2xl p-8">
          <div className="flex items-center gap-3 p-4 mb-6 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-amber-400">
            <ShieldAlert className="w-5 h-5 flex-shrink-0" />
            <p className="text-xs font-medium leading-relaxed">
              Authorized access only. All administrator activities are logged and monitored.
            </p>
          </div>

          <form onSubmit={handleAdminLogin} className="space-y-5">
            <div className="space-y-2">
              <Label htmlFor="admin-email" className="text-[#E2E8F0] font-semibold text-xs uppercase tracking-wider">
                Admin Email
              </Label>
              <Input
                id="admin-email"
                type="email"
                placeholder="admin@navgurukul.org"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="bg-[#0F172A]/50 border-[#334155] focus-visible:ring-[#5B5FEF] text-white placeholder-[#475569] rounded-xl py-6"
              />
            </div>

            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <Label htmlFor="admin-password" className="text-[#E2E8F0] font-semibold text-xs uppercase tracking-wider">
                  Password
                </Label>
              </div>
              <Input
                id="admin-password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="bg-[#0F172A]/50 border-[#334155] focus-visible:ring-[#5B5FEF] text-white placeholder-[#475569] rounded-xl py-6"
              />
            </div>

            <Button
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-to-r from-[#5B5FEF] to-[#8B7CF8] hover:from-[#4A4ED8] hover:to-[#7A6AE6] text-white py-6 text-md mt-6 rounded-xl active:scale-[0.98] transition-all shadow-lg shadow-[#5B5FEF]/20 font-semibold"
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                  Verifying Credentials...
                </>
              ) : (
                "Access Dashboard"
              )}
            </Button>
          </form>
        </div>

        <div className="text-center mt-6">
          <button
            onClick={() => router.push("/auth")}
            className="text-xs font-semibold text-[#94A3B8] hover:text-white transition-colors"
          >
            ← Back to Student & Mentor Portal
          </button>
        </div>
      </motion.div>
    </div>
  );
}
