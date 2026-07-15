"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, LogOut, MapPin, Shield, Mail } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { useAuthStore } from "@/store/authStore";
import { motion } from "framer-motion";

export default function ProfilePage() {
  const router = useRouter();
  const { user, isAuthenticated, logout } = useAuthStore();

  useEffect(() => {
    // BYPASS AUTH FOR TESTING
    // if (!isAuthenticated) {
    //   router.push("/auth");
    // }
  }, [isAuthenticated, router]);

  const handleLogout = () => {
    logout();
    router.push("/auth");
  };

  if (!user) return null;

  return (
    <div className="min-h-screen bg-[#FAFAFC]">
      <header className="flex items-center px-4 sm:px-6 py-4 bg-white/80 backdrop-blur-md border-b border-[#E8EAF5] sticky top-0 z-10">
        <Button variant="ghost" size="icon" onClick={() => router.push("/chat")} aria-label="Go back to chat" className="mr-4 active:scale-95 transition-transform hover:bg-[#F3F4F6] rounded-full">
          <ArrowLeft className="w-5 h-5 text-gray-500" />
        </Button>
        <h1 className="text-xl font-semibold tracking-tight text-gray-900">Student Profile</h1>
      </header>

      <main className="p-4 sm:p-6 max-w-3xl mx-auto mt-4 sm:mt-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
        >
          <Card className="border border-[#E8EAF5]/50 shadow-xl shadow-[#5B5FEF]/5 overflow-hidden rounded-3xl bg-white/90 backdrop-blur-sm">
            <div className="h-32 bg-gradient-to-r from-[#5B5FEF] to-[#8B7CF8]"></div>
            <div className="px-6 sm:px-10 pb-10 relative">
              <div className="absolute -top-16 border-4 border-white rounded-full shadow-md bg-white">
                <Avatar className="w-32 h-32">
                  <AvatarFallback className="bg-white text-[#5B5FEF] text-5xl font-bold">
                    {user.username?.charAt(0).toUpperCase()}
                  </AvatarFallback>
                </Avatar>
              </div>
              
              <div className="pt-20">
                <div className="flex flex-col sm:flex-row justify-between sm:items-start gap-4">
                  <div>
                    <h2 className="text-3xl font-bold tracking-tight text-gray-900">{user.username}</h2>
                    <p className="text-[#6B7280] text-sm font-semibold tracking-wider mt-1">{user.role.toUpperCase()}</p>
                  </div>
                  <Button variant="destructive" onClick={handleLogout} aria-label="Logout" className="rounded-full shadow-sm active:scale-95 transition-all self-start">
                    <LogOut className="w-4 h-4 mr-2" />
                    Logout
                  </Button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6 mt-10">
                  <motion.div 
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.3, delay: 0.2 }}
                    className="flex items-center gap-4 p-5 rounded-2xl border border-[#E8EAF5] bg-white shadow-sm hover:shadow-md transition-shadow"
                  >
                    <div className="w-12 h-12 rounded-full bg-[#FAFAFC] flex items-center justify-center text-[#5B5FEF] shadow-inner">
                      <Mail className="w-5 h-5" />
                    </div>
                    <div>
                      <p className="text-xs text-gray-400 font-semibold uppercase tracking-wide">Email Address</p>
                      <p className="font-medium text-gray-800 mt-0.5">{user.email}</p>
                    </div>
                  </motion.div>

                  <motion.div 
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.3, delay: 0.3 }}
                    className="flex items-center gap-4 p-5 rounded-2xl border border-[#E8EAF5] bg-white shadow-sm hover:shadow-md transition-shadow"
                  >
                    <div className="w-12 h-12 rounded-full bg-[#FAFAFC] flex items-center justify-center text-[#5B5FEF] shadow-inner">
                      <MapPin className="w-5 h-5" />
                    </div>
                    <div>
                      <p className="text-xs text-gray-400 font-semibold uppercase tracking-wide">Campus</p>
                      <p className="font-medium text-gray-800 mt-0.5">{user.campus || "Unassigned"}</p>
                    </div>
                  </motion.div>

                  <motion.div 
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.3, delay: 0.4 }}
                    className="flex items-center gap-4 p-5 rounded-2xl border border-[#E8EAF5] bg-white shadow-sm hover:shadow-md transition-shadow md:col-span-2 lg:col-span-1"
                  >
                    <div className="w-12 h-12 rounded-full bg-[#FAFAFC] flex items-center justify-center text-[#5B5FEF] shadow-inner">
                      <Shield className="w-5 h-5" />
                    </div>
                    <div>
                      <p className="text-xs text-gray-400 font-semibold uppercase tracking-wide">House</p>
                      <p className="font-medium text-gray-800 mt-0.5">{user.house || "Unassigned"}</p>
                    </div>
                  </motion.div>
                </div>
              </div>
            </div>
          </Card>
        </motion.div>
      </main>
    </div>
  );
}
