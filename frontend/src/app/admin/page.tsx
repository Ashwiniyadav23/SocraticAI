"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import api from "@/lib/api";
import { useAuthStore } from "@/store/authStore";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { 
  Users, UserCheck, GraduationCap, MessagesSquare, Cpu, 
  Search, ShieldAlert, LogOut, Check, X, RefreshCw, Eye
} from "lucide-react";
import { motion } from "framer-motion";

interface UserData {
  id: string;
  email: string;
  role: string;
  status: string;
  created_at?: string;
}

interface PlatformStats {
  total_students: number;
  total_mentors: number;
  active_users: number;
  total_sessions: number;
  ai_usage: number;
}

export default function AdminDashboard() {
  const router = useRouter();
  const { user, isAuthenticated, logout } = useAuthStore();
  const [mentors, setMentors] = useState<UserData[]>([]);
  const [students, setStudents] = useState<UserData[]>([]);
  const [stats, setStats] = useState<PlatformStats | null>(null);
  const [loading, setLoading] = useState(true);

  // Search & Filter state
  const [mentorSearch, setMentorSearch] = useState("");
  const [studentSearch, setStudentSearch] = useState("");
  const [mentorStatusFilter, setMentorStatusFilter] = useState("all");

  useEffect(() => {
    // 1. Strict route protection: Redirection to /admin/login
    if (!isAuthenticated) {
      router.push("/admin/login");
      return;
    }
    if (user?.role !== "admin") {
      toast.error("Access denied. Admins only.");
      router.push("/chat");
      return;
    }

    fetchDashboardData();
  }, [user, isAuthenticated]);

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      await Promise.all([fetchStats(), fetchMentors(), fetchStudents()]);
    } catch (error) {
      toast.error("Error loading dashboard data.");
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const { data } = await api.get("/v1/admin/stats");
      setStats(data);
    } catch (e) {
      console.error("Failed to fetch platform stats", e);
    }
  };

  const fetchMentors = async () => {
    try {
      const { data } = await api.get("/v1/admin/mentors");
      setMentors(data);
    } catch (e) {
      console.error("Failed to fetch mentors", e);
    }
  };

  const fetchStudents = async () => {
    try {
      const { data } = await api.get("/v1/admin/students");
      setStudents(data);
    } catch (e) {
      console.error("Failed to fetch students", e);
    }
  };

  // Actions
  const handleApprove = async (id: string) => {
    try {
      await api.post(`/v1/admin/mentors/${id}/approve`);
      toast.success("Mentor request approved!");
      fetchMentors();
      fetchStats();
    } catch (err) {
      toast.error("Failed to approve mentor");
    }
  };

  const handleReject = async (id: string) => {
    try {
      await api.post(`/v1/admin/mentors/${id}/reject`);
      toast.success("Mentor request rejected.");
      fetchMentors();
      fetchStats();
    } catch (err) {
      toast.error("Failed to reject mentor");
    }
  };

  const handleDeactivate = async (id: string) => {
    try {
      await api.post(`/v1/admin/mentors/${id}/deactivate`);
      toast.success("Mentor account suspended.");
      fetchMentors();
      fetchStats();
    } catch (err) {
      toast.error("Failed to deactivate mentor");
    }
  };

  const handleActivate = async (id: string) => {
    try {
      await api.post(`/v1/admin/mentors/${id}/activate`);
      toast.success("Mentor account reactivated!");
      fetchMentors();
      fetchStats();
    } catch (err) {
      toast.error("Failed to activate mentor");
    }
  };

  const handleLogout = () => {
    logout();
    router.push("/admin/login");
  };

  // Filtering lists
  const filteredMentors = mentors.filter((m) => {
    const matchesSearch = m.email.toLowerCase().includes(mentorSearch.toLowerCase());
    const matchesStatus = mentorStatusFilter === "all" || m.status === mentorStatusFilter;
    return matchesSearch && matchesStatus;
  });

  const filteredStudents = students.filter((s) => {
    return s.email.toLowerCase().includes(studentSearch.toLowerCase());
  });

  if (loading) {
    return (
      <div className="min-h-screen bg-[#F8FAFC] flex flex-col items-center justify-center gap-4">
        <RefreshCw className="w-10 h-10 text-[#5B5FEF] animate-spin" />
        <p className="text-sm font-semibold text-gray-500">Loading Admin Control Panel...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#FAFAFC] text-gray-900 pb-12">
      {/* Premium Header */}
      <header className="bg-white border-b border-[#E8EAF5] sticky top-0 z-30 shadow-sm shadow-[#5B5FEF]/2">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#5B5FEF] to-[#8B7CF8] flex items-center justify-center text-white font-extrabold text-xl shadow-md">
              A
            </div>
            <div>
              <h1 className="text-lg font-bold tracking-tight text-gray-950 flex items-center gap-2">
                Astra Dashboard
                <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 bg-red-100 text-red-700 rounded-full border border-red-200">
                  Admin
                </span>
              </h1>
              <p className="text-xs text-gray-500 font-medium">Platform Management & Insights</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Button 
              variant="outline" 
              onClick={() => router.push("/chat")} 
              className="text-xs font-semibold px-4 py-2 border-[#E8EAF5] hover:bg-gray-50 rounded-lg"
            >
              ← Back to Chat
            </Button>
            <Button 
              variant="destructive" 
              size="sm" 
              onClick={handleLogout} 
              className="text-xs font-bold rounded-lg flex items-center gap-2"
            >
              <LogOut className="w-4 h-4" />
              Logout
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 mt-8 space-y-8">
        {/* Statistics Section */}
        <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-6">
          <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
            <Card className="border border-[#E8EAF5] shadow-sm hover:shadow-md transition-shadow rounded-2xl bg-white overflow-hidden relative group">
              <div className="absolute top-0 left-0 w-1.5 h-full bg-[#5B5FEF]" />
              <CardContent className="p-6 flex items-center justify-between">
                <div>
                  <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Total Students</p>
                  <h3 className="text-3xl font-extrabold text-gray-900 mt-2">{stats?.total_students ?? 0}</h3>
                </div>
                <div className="w-12 h-12 rounded-xl bg-[#5B5FEF]/10 flex items-center justify-center text-[#5B5FEF]">
                  <GraduationCap className="w-6 h-6" />
                </div>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3, delay: 0.05 }}>
            <Card className="border border-[#E8EAF5] shadow-sm hover:shadow-md transition-shadow rounded-2xl bg-white overflow-hidden relative group">
              <div className="absolute top-0 left-0 w-1.5 h-full bg-[#8B7CF8]" />
              <CardContent className="p-6 flex items-center justify-between">
                <div>
                  <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Total Mentors</p>
                  <h3 className="text-3xl font-extrabold text-gray-900 mt-2">{stats?.total_mentors ?? 0}</h3>
                </div>
                <div className="w-12 h-12 rounded-xl bg-[#8B7CF8]/10 flex items-center justify-center text-[#8B7CF8]">
                  <Users className="w-6 h-6" />
                </div>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3, delay: 0.1 }}>
            <Card className="border border-[#E8EAF5] shadow-sm hover:shadow-md transition-shadow rounded-2xl bg-white overflow-hidden relative group">
              <div className="absolute top-0 left-0 w-1.5 h-full bg-emerald-500" />
              <CardContent className="p-6 flex items-center justify-between">
                <div>
                  <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Active Users</p>
                  <h3 className="text-3xl font-extrabold text-gray-900 mt-2">{stats?.active_users ?? 0}</h3>
                </div>
                <div className="w-12 h-12 rounded-xl bg-emerald-500/10 flex items-center justify-center text-emerald-600">
                  <UserCheck className="w-6 h-6" />
                </div>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3, delay: 0.15 }}>
            <Card className="border border-[#E8EAF5] shadow-sm hover:shadow-md transition-shadow rounded-2xl bg-white overflow-hidden relative group">
              <div className="absolute top-0 left-0 w-1.5 h-full bg-indigo-500" />
              <CardContent className="p-6 flex items-center justify-between">
                <div>
                  <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Total Sessions</p>
                  <h3 className="text-3xl font-extrabold text-gray-900 mt-2">{stats?.total_sessions ?? 0}</h3>
                </div>
                <div className="w-12 h-12 rounded-xl bg-indigo-500/10 flex items-center justify-center text-indigo-600">
                  <MessagesSquare className="w-6 h-6" />
                </div>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3, delay: 0.2 }}>
            <Card className="border border-[#E8EAF5] shadow-sm hover:shadow-md transition-shadow rounded-2xl bg-white overflow-hidden relative group">
              <div className="absolute top-0 left-0 w-1.5 h-full bg-amber-500" />
              <CardContent className="p-6 flex items-center justify-between">
                <div>
                  <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">AI Coach Turns</p>
                  <h3 className="text-3xl font-extrabold text-gray-900 mt-2">{stats?.ai_usage ?? 0}</h3>
                </div>
                <div className="w-12 h-12 rounded-xl bg-amber-500/10 flex items-center justify-center text-amber-600">
                  <Cpu className="w-6 h-6" />
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </section>

        {/* Tab System for lists */}
        <section className="bg-white rounded-2xl border border-[#E8EAF5] shadow-sm overflow-hidden p-6 sm:p-8">
          <Tabs defaultValue="mentors" className="w-full">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-gray-100 pb-4 mb-6">
              <TabsList className="bg-gray-100/80 p-1 rounded-xl">
                <TabsTrigger value="mentors" className="px-5 py-2.5 rounded-lg text-sm font-semibold transition-all">
                  Mentors Management ({mentors.length})
                </TabsTrigger>
                <TabsTrigger value="students" className="px-5 py-2.5 rounded-lg text-sm font-semibold transition-all">
                  Students ({students.length})
                </TabsTrigger>
              </TabsList>

              <button 
                onClick={fetchDashboardData} 
                className="text-xs font-semibold text-[#5B5FEF] hover:text-[#4A4ED8] flex items-center gap-1.5 border border-[#5B5FEF]/10 hover:bg-[#5B5FEF]/5 px-3 py-2 rounded-lg transition-colors"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                Refresh Data
              </button>
            </div>

            {/* Mentors Panel */}
            <TabsContent value="mentors" className="space-y-6 outline-none">
              {/* Mentors Filter Toolbar */}
              <div className="flex flex-col sm:flex-row gap-4">
                <div className="relative flex-1">
                  <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <Input
                    placeholder="Search mentors by email..."
                    value={mentorSearch}
                    onChange={(e) => setMentorSearch(e.target.value)}
                    className="pl-10 rounded-xl bg-gray-50/50 border-[#E8EAF5]"
                  />
                </div>
                <div className="flex items-center gap-2">
                  <label className="text-xs font-bold text-gray-400 uppercase tracking-wider flex-shrink-0">Status:</label>
                  <select
                    value={mentorStatusFilter}
                    onChange={(e) => setMentorStatusFilter(e.target.value)}
                    className="bg-gray-50 border border-[#E8EAF5] rounded-xl px-4 py-2 text-sm font-semibold outline-none focus:border-[#5B5FEF] transition-colors"
                  >
                    <option value="all">All Statuses</option>
                    <option value="pending">Pending Requests</option>
                    <option value="active">Active Mentors</option>
                    <option value="suspended">Suspended Mentors</option>
                    <option value="rejected">Rejected Requests</option>
                  </select>
                </div>
              </div>

              {/* Mentors Table */}
              <div className="overflow-x-auto rounded-xl border border-gray-100">
                <table className="w-full text-left">
                  <thead className="bg-gray-50 border-b border-gray-100">
                    <tr>
                      <th className="px-6 py-4 text-xs font-bold text-gray-400 uppercase tracking-wider">Mentor Email</th>
                      <th className="px-6 py-4 text-xs font-bold text-gray-400 uppercase tracking-wider">Role</th>
                      <th className="px-6 py-4 text-xs font-bold text-gray-400 uppercase tracking-wider">Status</th>
                      <th className="px-6 py-4 text-xs font-bold text-gray-400 uppercase tracking-wider text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-50 bg-white">
                    {filteredMentors.map((m) => (
                      <tr key={m.id} className="hover:bg-gray-50/40 transition-colors">
                        <td className="px-6 py-4 font-semibold text-gray-800">{m.email}</td>
                        <td className="px-6 py-4">
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-[#8B7CF8]/10 text-[#8B7CF8]">
                            {m.role}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold ${
                            m.status === 'active' ? 'bg-emerald-100 text-emerald-800' : 
                            m.status === 'pending' ? 'bg-amber-100 text-amber-800' : 
                            m.status === 'suspended' ? 'bg-orange-100 text-orange-800' : 
                            'bg-red-100 text-red-800'
                          }`}>
                            {m.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-right space-x-2">
                          {m.status === 'pending' && (
                            <>
                              <Button 
                                size="sm" 
                                onClick={() => handleApprove(m.id)} 
                                className="bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg px-3 py-1.5 h-8 font-semibold text-xs"
                              >
                                <Check className="w-3.5 h-3.5 mr-1" />
                                Approve
                              </Button>
                              <Button 
                                size="sm" 
                                variant="outline"
                                onClick={() => handleReject(m.id)} 
                                className="text-red-600 border-red-100 hover:bg-red-50 rounded-lg px-3 py-1.5 h-8 font-semibold text-xs"
                              >
                                <X className="w-3.5 h-3.5 mr-1" />
                                Reject
                              </Button>
                            </>
                          )}
                          {m.status === 'active' && (
                            <Button 
                              size="sm" 
                              variant="outline"
                              onClick={() => handleDeactivate(m.id)} 
                              className="text-orange-600 border-orange-100 hover:bg-orange-50 rounded-lg px-3 py-1.5 h-8 font-semibold text-xs"
                            >
                              Deactivate
                            </Button>
                          )}
                          {(m.status === 'suspended' || m.status === 'rejected') && (
                            <Button 
                              size="sm" 
                              onClick={() => handleActivate(m.id)} 
                              className="bg-[#5B5FEF] hover:bg-[#4A4ED8] text-white rounded-lg px-3 py-1.5 h-8 font-semibold text-xs"
                            >
                              Activate
                            </Button>
                          )}
                        </td>
                      </tr>
                    ))}
                    {filteredMentors.length === 0 && (
                      <tr>
                        <td colSpan={4} className="px-6 py-12 text-center text-gray-400 font-medium">
                          No mentors matching the filter or search were found.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </TabsContent>

            {/* Students Panel */}
            <TabsContent value="students" className="space-y-6 outline-none">
              {/* Students Filter Toolbar */}
              <div className="flex">
                <div className="relative flex-1">
                  <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <Input
                    placeholder="Search students by email..."
                    value={studentSearch}
                    onChange={(e) => setStudentSearch(e.target.value)}
                    className="pl-10 rounded-xl bg-gray-50/50 border-[#E8EAF5]"
                  />
                </div>
              </div>

              {/* Students Table */}
              <div className="overflow-x-auto rounded-xl border border-gray-100">
                <table className="w-full text-left">
                  <thead className="bg-gray-50 border-b border-gray-100">
                    <tr>
                      <th className="px-6 py-4 text-xs font-bold text-gray-400 uppercase tracking-wider">Student Email</th>
                      <th className="px-6 py-4 text-xs font-bold text-gray-400 uppercase tracking-wider">Role</th>
                      <th className="px-6 py-4 text-xs font-bold text-gray-400 uppercase tracking-wider">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-50 bg-white">
                    {filteredStudents.map((s) => (
                      <tr key={s.id} className="hover:bg-gray-50/40 transition-colors">
                        <td className="px-6 py-4 font-semibold text-gray-800">{s.email}</td>
                        <td className="px-6 py-4">
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-[#5B5FEF]/10 text-[#5B5FEF]">
                            {s.role}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800">
                            {s.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                    {filteredStudents.length === 0 && (
                      <tr>
                        <td colSpan={3} className="px-6 py-12 text-center text-gray-400 font-medium">
                          No students matching the search were found.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </TabsContent>
          </Tabs>
        </section>
      </main>
    </div>
  );
}
