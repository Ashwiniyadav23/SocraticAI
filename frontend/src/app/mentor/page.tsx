"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import api from "@/lib/api";
import { useAuthStore } from "@/store/authStore";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Loader2, Search, Brain, Target, Sparkles, TrendingUp, AlertCircle, CheckCircle2 } from "lucide-react";
import { motion } from "framer-motion";

interface StudentData {
  student_id: string;
  email: string;
  mastery_summary: { concept_id: string; score: number }[];
  confidence: number;
  ai_dependency: number;
  curiosity_score: number;
  independent_thinking: number;
  learning_velocity: number;
  weak_concepts: string[];
  strong_concepts: string[];
}

export default function MentorDashboard() {
  const router = useRouter();
  const { user, isAuthenticated } = useAuthStore();
  const [students, setStudents] = useState<StudentData[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    if (!isAuthenticated) {
      router.push("/auth");
      return;
    }
    if (user?.role !== "mentor") {
      toast.error("Access denied. Mentors only.");
      router.push("/chat");
      return;
    }
    if (user?.status !== "active") {
      toast.error("Your mentor account is pending approval.");
      router.push("/auth");
      return;
    }

    fetchStudents();
  }, [user, isAuthenticated]);

  const fetchStudents = async () => {
    try {
      const { data } = await api.get("/v1/mentor/students");
      setStudents(data);
    } catch (error: any) {
      if (error.response?.status === 403) {
         toast.error("Access denied. Mentor account might be pending.");
         router.push("/auth");
      } else {
         toast.error("Failed to fetch students");
      }
    } finally {
      setLoading(false);
    }
  };

  const filteredStudents = students.filter(s => 
    s.email.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center bg-[#FAFAFC]">
      <Loader2 className="w-8 h-8 text-[#5B5FEF] animate-spin" />
    </div>
  );

  return (
    <div className="min-h-screen bg-[#FAFAFC] p-8">
      <div className="max-w-7xl mx-auto space-y-8">
        
        <header className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-gray-900">Mentor Dashboard</h1>
            <p className="text-gray-500 mt-1">Monitor student progress and behavioral insights across the platform.</p>
          </div>
          
          <div className="relative w-full md:w-72">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <Input 
              placeholder="Search students by email..." 
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9 border-gray-200 focus-visible:ring-[#5B5FEF] bg-white"
            />
          </div>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card className="border-none shadow-sm shadow-[#5B5FEF]/5 bg-white">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-gray-500">Total Students</CardTitle>
              <div className="w-8 h-8 rounded-full bg-blue-50 flex items-center justify-center text-blue-500">
                <Target className="w-4 h-4" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-gray-900">{students.length}</div>
            </CardContent>
          </Card>
        </div>

        <div className="space-y-4">
          <h2 className="text-xl font-semibold text-gray-900">Student Insights</h2>
          
          {filteredStudents.length === 0 ? (
            <div className="text-center py-12 bg-white rounded-xl border border-gray-100 shadow-sm">
              <p className="text-gray-500">No students found.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-6">
              {filteredStudents.map((student, i) => (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.05 }}
                  key={student.student_id}
                >
                  <Card className="border border-gray-100 shadow-sm hover:shadow-md transition-shadow bg-white overflow-hidden">
                    <div className="p-6">
                      <div className="flex flex-col md:flex-row md:items-start justify-between gap-6">
                        
                        {/* Student Profile Info */}
                        <div className="w-full md:w-1/4 space-y-4 border-b md:border-b-0 md:border-r border-gray-100 pb-4 md:pb-0 md:pr-6">
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[#5B5FEF] to-[#8B7CF8] flex items-center justify-center text-white font-bold shadow-sm">
                              {student.email.charAt(0).toUpperCase()}
                            </div>
                            <div>
                              <h3 className="font-semibold text-gray-900 truncate" title={student.email}>
                                {student.email.split('@')[0]}
                              </h3>
                              <p className="text-xs text-gray-500 truncate">{student.email}</p>
                            </div>
                          </div>
                          
                          <div className="pt-2">
                            <p className="text-sm font-medium text-gray-700 mb-2">Mastery Progress</p>
                            <div className="space-y-2">
                              {student.mastery_summary.length > 0 ? student.mastery_summary.slice(0,3).map(m => (
                                <div key={m.concept_id} className="flex items-center justify-between text-xs">
                                  <span className="text-gray-500 truncate pr-2 max-w-[120px]" title={m.concept_id}>
                                    {m.concept_id.split('-')[0]}
                                  </span>
                                  <span className="font-medium text-gray-900">{(m.score * 100).toFixed(0)}%</span>
                                </div>
                              )) : (
                                <div className="text-xs text-gray-400">No mastery data yet.</div>
                              )}
                            </div>
                          </div>
                        </div>

                        {/* Behavioral Metrics Grid */}
                        <div className="w-full md:w-3/4">
                           <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                              
                              <div className="bg-gray-50 rounded-lg p-3 border border-gray-100">
                                <div className="flex items-center gap-2 mb-1">
                                  <Brain className="w-3.5 h-3.5 text-purple-500" />
                                  <span className="text-xs font-medium text-gray-600 uppercase tracking-wider">Independent</span>
                                </div>
                                <div className="text-lg font-semibold text-gray-900">
                                  {(student.independent_thinking * 100).toFixed(0)}%
                                </div>
                              </div>
                              
                              <div className="bg-gray-50 rounded-lg p-3 border border-gray-100">
                                <div className="flex items-center gap-2 mb-1">
                                  <Sparkles className="w-3.5 h-3.5 text-yellow-500" />
                                  <span className="text-xs font-medium text-gray-600 uppercase tracking-wider">Curiosity</span>
                                </div>
                                <div className="text-lg font-semibold text-gray-900">
                                  {(student.curiosity_score * 100).toFixed(0)}%
                                </div>
                              </div>
                              
                              <div className="bg-gray-50 rounded-lg p-3 border border-gray-100">
                                <div className="flex items-center gap-2 mb-1">
                                  <TrendingUp className="w-3.5 h-3.5 text-green-500" />
                                  <span className="text-xs font-medium text-gray-600 uppercase tracking-wider">Velocity</span>
                                </div>
                                <div className="text-lg font-semibold text-gray-900">
                                  {(student.learning_velocity * 100).toFixed(0)}%
                                </div>
                              </div>
                              
                              <div className="bg-gray-50 rounded-lg p-3 border border-gray-100">
                                <div className="flex items-center gap-2 mb-1">
                                  <AlertCircle className={`w-3.5 h-3.5 ${student.ai_dependency > 0.7 ? 'text-red-500' : 'text-blue-500'}`} />
                                  <span className="text-xs font-medium text-gray-600 uppercase tracking-wider">AI Dep.</span>
                                </div>
                                <div className={`text-lg font-semibold ${student.ai_dependency > 0.7 ? 'text-red-600' : 'text-gray-900'}`}>
                                  {(student.ai_dependency * 100).toFixed(0)}%
                                </div>
                              </div>
                           </div>

                           {/* Weak/Strong Concepts */}
                           <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                              <div>
                                <h4 className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2 flex items-center gap-1">
                                  <CheckCircle2 className="w-3 h-3 text-green-500" /> Strong Concepts
                                </h4>
                                <div className="flex flex-wrap gap-1.5">
                                  {student.strong_concepts && student.strong_concepts.length > 0 ? (
                                    student.strong_concepts.map(c => (
                                      <span key={c} className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium bg-green-50 text-green-700 border border-green-100">
                                        {c}
                                      </span>
                                    ))
                                  ) : (
                                    <span className="text-xs text-gray-400">None identified</span>
                                  )}
                                </div>
                              </div>
                              <div>
                                <h4 className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2 flex items-center gap-1">
                                  <AlertCircle className="w-3 h-3 text-orange-500" /> Weak Concepts
                                </h4>
                                <div className="flex flex-wrap gap-1.5">
                                  {student.weak_concepts && student.weak_concepts.length > 0 ? (
                                    student.weak_concepts.map(c => (
                                      <span key={c} className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium bg-orange-50 text-orange-700 border border-orange-100">
                                        {c}
                                      </span>
                                    ))
                                  ) : (
                                    <span className="text-xs text-gray-400">None identified</span>
                                  )}
                                </div>
                              </div>
                           </div>
                        </div>

                      </div>
                    </div>
                  </Card>
                </motion.div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
